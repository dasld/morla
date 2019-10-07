# -*- coding: utf-8 -*-

from typing import Any, Callable, List, Iterable, Optional, Union, Tuple

# sys is already loaded by tkinter; see below
import os

import io
from logging import CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
import logging

# import base64
from functools import partial, wraps
import json

# import webbrowser as browser

from tkinter import re, sys
from tkinter import filedialog  # messagebox
from tkinter.constants import N, S, E, W, RAISED, SUNKEN, FLAT, RIDGE, GROOVE, SOLID
from tkinter import ttk  # import Notebook
import tkinter as tk

# import Pmw

from morla.utils import *
from morla.configuration import Configuration
from morla.preference import Preferences
from morla.bulk import Parser
from morla.gui import *
from morla.tooltip import Tooltip
from morla.morla_logging import init_logger
import morla


# custom type
# tk.Text = TypeVar("tk.Text", tk.Text, ScrolledText)

# can only be set to False by MorlaFrame.actually_quit
# MORLA_RUNNING = True

# dimensions
# X_FACTOR = 0.66
# Y_FACTOR = 0.75
TEXT_HEIGHT = 20
TEXT_WIDTH = 40

# fonts and cursors
HEADER_FONT = ("Helvetica", "16", "bold")
SANS_FONT = ("Helvetica", "12")
MONO_FONT = ("Courier", "11")  # , NORMAL)
# MONO_FONT = "TkFixedFont"  # "-*-courier-medium-r-*-*-12-*-*-*-*-*-*-*"
# MONO_FONT = "-*-lucidatypewriter-medium-r-*-*-*-140-*-*-*-*-*-*"
# MONO_FONT = "-*-terminal-medium-*-*-*-14-*-*-*-*-*-*-*"
SERIF_FONT = "-*-times-medium-r-*-*-12-*-*-*-*-*-*-*"
CURSOR_GREEN = "#45F700"
CURSOR_RED = "#990000"  # "#CD0101"

# default symbols
# https://stackoverflow.com/a/37799580
ERROR_SYMBOL = "::tk::icons::error"
WARNING_SYMBOL = "::tk::icons::warning"
INFO_SYMBOL = "::tk::icons::information"
QUESTION_SYMBOL = "::tk::icons::question"

# internal data
HERE = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(HERE, "..", "data", "logo.gif")
LANGUAGE_PATH = os.path.join(HERE, "..", "data", "languages.json")


class MorlaError(Exception):
    pass


def divert2log(f: Callable) -> Callable:
    """Decorator to be used exclusively by MorlaFrame instances; it is here, and not as
    a MorlaFrame staticmethod, because I can't make it work as a static method.
    """

    @wraps(f)
    def wrapper(*args, **kwargs) -> Any:
        content = io.StringIO()
        with redirect_stdout(content), redirect_stderr(content):
            output = f(*args, **kwargs)
            try:
                self = args[0]
                self.log(CRITICAL, content.getvalue())
            except (IndexError, AttributeError):
                    raise MorlaError(
                        "divert2log can only be called by a MorlaFrame method!"
                    )
            if False:
                try:
                    log_ScrolledText = args[0].log_text  # .Text
                except (IndexError, AttributeError):
                    raise MorlaError(
                        "divert2log can only be called by a MorlaFrame method!"
                    )
                else:
                    typeset_Text(content.getvalue(), log_ScrolledText, mode="a")
        return output

    return wrapper


class MorlaFrame(tk.Frame):
    ftypes = [("LaTeX files", "*.tex"), ("Text files", "*.txt"), ("All files", "*")]

    def reorder_ftypes(self, ext: str) -> List[Tuple[str]]:
        for pair in self.ftypes:
            if pair[1].endswith(ext):
                make_first(pair, self.ftypes)
                break
        return self.ftypes

    def __init__(self, cmdline_arg: Optional[str] = "") -> None:
        master = tk.Tk()
        super(MorlaFrame, self).__init__(master)
        self.master = master
        # set the HOME_DIR
        # https://stackoverflow.com/a/10644400
        if os.name == "posix":
            self.home_dir = os.path.expanduser("~")
        elif os.name == "nt":
            from win32com.shell import shellcon, shell

            self.home_dir = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
        else:
            self.home_dir = HERE
        if not self.home_dir.endswith(os.sep):
            self.home_dir += os.sep
        self.log(DEBUG, f"home dir: {self.home_dir}")
        # set up the morla directory
        self.app_dir = "." if os.name != "nt" else ""
        self.app_dir += morla.SELETOR_NAME.lower().replace(" ", "-") + os.sep
        self.full_app_dir = os.path.join(self.home_dir, self.app_dir)
        if not os.path.isdir(self.full_app_dir):
            self.log(INFO, f"creating {self.full_app_dir}")
            os.mkdir(self.full_app_dir)
        self.log(DEBUG, f"app dir: {self.app_dir}")
        self.log(DEBUG, f"full app dir: {self.full_app_dir}")
        # both home_dir and app_dir end with os.sep
        # set a Preferences object
        prefs_path = "preferences.ini"
        with Cd(self.full_app_dir):
            self.preferences = Preferences(os.getcwd())
            if os.path.exists(prefs_path):
                try:
                    self.preferences.read(prefs_path)
                except:
                    self.log(CRITICAL, f"reading {prefs_path} failed!")
                    raise
                else:
                    self.log(INFO, f"reading {prefs_path} succeeded!")
                    with open(prefs_path, "r") as ini_file:
                        content = ini_file.read().strip()
                        self.log(INFO, EOL + content)
            else:
                self.preferences.save()
        # language
        with open(LANGUAGE_PATH, "r") as json_file:
            language_dict = json.load(json_file)
        if are_subdicts_invalid(language_dict):
            msg = f"reading {prefs_path} failed!"
            self.log(CRITICAL, msg)
            raise MorlaError(msg)
        self.language_dict = language_dict
        # menubars and widgets
        self.init_menubar()
        self.init_widgets()
        # set up a logger
        log_path = os.path.join(self.full_app_dir, morla.SELETOR_NAME.lower() + ".log")
        self.logger = init_logger(log_path, self.log_text)
        self.log(DEBUG, f"log_path: {log_path}")
        # icon
        icon_path = ICON_PATH
        # with open(icon_path, "rb") as icon:
        #       data = io.BytesIO()
        #       base64.encode(logo, data)
        #       string = data.getvalue().decode(UTF8)
        try:
            icon = tk.PhotoImage(file=icon_path)
        except tk.TclError:
            self.log(WARNING, f"Couldn't load {icon_path}")
            self.icon = None
        else:
            master.tk.call("wm", "iconphoto", master._w, icon)
            self.icon = icon
        # misc settings
        master.protocol("WM_DELETE_WINDOW", self.prompt_quit)
        master.title(morla.SELETOR_NAME)
        # create a default Configuration
        self.configs = Configuration()
        # create a parser
        self.parser = Parser()
        # set a minimum size, allow resizing, and display everything
        # master.attributes("-fullscreen", True)
        master.resizable(True, True)  # (False, False)
        # resizing is twice as fast horizontally
        master.grid_rowconfigure(0, weight=2)
        master.grid_columnconfigure(0, weight=1)
        for row in (1, 2):
            self.grid_rowconfigure(row, weight=2)
        for col in range(4):
            self.grid_columnconfigure(col, weight=1)
        self.grid(row=0, column=0, sticky=(N, S, E, W))
        master.deiconify()
        # master.geometry() will return "1x1+0+0" here
        master.update()
        # now master.geometry() returns valid size/placement
        master.minsize(master.winfo_width(), master.winfo_height())
        center(master)
        # load the file given as argument, if any
        if cmdline_arg:
            if not isinstance(cmdline_arg, str):
                raise TypeError
            self.open_file(cmdline_arg)
        else:
            self.last_dir = self.home_dir
            self.last_ext = "*"

    def log(self, level, msg, *args, **kwargs) -> None:
        try:
            self.logger.log(level, msg, *args, **kwargs)
        except Exception as e:
            print("logging failed:", e)
            level_name = logging.getLevelName(level)
            print(level_name, msg)
        else:
            pass
            self.logger.debug("logging succeded")

    def get_string(
        self, key: str, lang: Optional[str] = None, capitalize: Optional[bool] = True
    ) -> str:
        """Fetches a string from the language dictionary that has been loaded from a
        JSON file.
        """
        if not lang:
            lang = self.preferences.get_section()["language"]
        value = self.language_dict[lang][key]
        if capitalize:
            value = capitalize_first(value)  # .capitalize()
        return value

    def prompt_quit(self) -> None:
        # if tk.messagebox.askokcancel("Quit", "Do you really want to quit?"):
        wish_to_quit = self.get_string("wish_to_quit")
        quit_word = self.get_string("quit")
        if self.pop_yesno(wish_to_quit, title=quit_word):
            self.actually_quit()

    def actually_quit(self) -> None:
        logging.shutdown()
        # https://stackoverflow.com/a/36291907
        for h in self.logger.handlers:
            if isinstance(h, logging.FileHandler):
                h.close()
        # self.quit()
        self.master.destroy()

    def set_exercises_button(self, value: bool) -> None:
        if isinstance(value, str):
            raise TypeError
        exercises_word = self.get_string("exercises")
        new_state = "normal" if value else "disabled"
        try:
            self.menubar.entryconfig(exercises_word, state=new_state)
        except AttributeError:
            raise MorlaError

    def init_menubar(self) -> None:
        # tearoff=0 keeps the user from detaching the Menu
        self.menubar = tk.Menu(self.master, relief=GROOVE, tearoff=0)
        self.master.config(menu=self.menubar)
        # file cascade
        fileMenu = tk.Menu(self.menubar, tearoff=0)
        file_word = self.get_string("file")
        self.menubar.add_cascade(label=file_word, menu=fileMenu)
        open_word = self.get_string("open") + LDOTS
        fileMenu.add_command(label=open_word, command=self.on_open_file)
        save_word = self.get_string("save") + LDOTS
        fileMenu.add_command(label=save_word, command=self.on_save_file)
        quit_word = self.get_string("quit")
        fileMenu.add_command(label=quit_word, command=self.prompt_quit)
        # configs "button"
        configurations_word = self.get_string("configurations")
        self.menubar.add_command(label=configurations_word, command=self.open_configs)
        # preferences "button"
        preferences_word = self.get_string("preferences")
        self.menubar.add_command(label=preferences_word, command=self.open_preferences)
        # Exercises "button"
        exercises_word = self.get_string("exercises")
        self.menubar.add_command(label=exercises_word, command=lambda *a, **kw: None)
        self.set_exercises_button(False)
        # menubar.entryconfig(exercises_word, state="disabled")
        # about "button"
        about_word = self.get_string("about")
        self.menubar.add_command(label=about_word, command=self.open_about_window)
        # Test2
        # print(type(self.menubar.entrycget(0)))
        # self.menubar_hoverinfo = HoverInfo(self.menubar, "You are\n hovering!", 500)
        # self.menubar_hoverinfo = Pmw.Baloon()
        self.menubar_hoverinfo = Tooltip(self.menubar, f"You are{EOL}hovering!")
        # print(dir(self.menubar_hoverinfo))
        # print(help(self.menubar_hoverinfo.unpost))

    def init_widgets(self) -> None:
        # "input" header
        # grid(0, 0)
        input_word = self.get_string("input")
        self.input_header = tk.Label(
            self, text=input_word, height="1", font=HEADER_FONT
        )
        self.input_header.grid(row=0, column=0, pady=BORDER)
        # "parse" button
        # grid(0, 1)
        parse_word = self.get_string("parse")
        self.parseButton = CustomButton(
            self, text=parse_word, command=self.on_parseButton_press
        )
        self.parseButton.grid(row=0, column=1)
        # "output" header
        # grid(0, 2)
        output_word = self.get_string("output")
        self.output_header = tk.Label(
            self, text=output_word, height="1", font=HEADER_FONT
        )
        self.output_header.grid(row=0, column=2, pady=BORDER)
        # "format" button
        # grid(0, 3)
        format_word = self.get_string("format")
        self.formatButton = CustomButton(
            self, text=format_word, command=self.on_formatButton_press
        )
        self.formatButton.grid(row=0, column=3)
        # input area
        # grid(1, 0-1)
        self.input_text = ScrolledText(
            self, height=TEXT_HEIGHT, width=TEXT_WIDTH, font=SANS_FONT
        )
        self.input_text.grid(
            row=1, column=0, columnspan=2, sticky=(N, E, W), padx=BORDER, pady=BORDER
        )
        # self.columnconfigure(0, weight=1)
        # output area
        # grid(1, 2-3)
        self.output_text = ScrolledText(
            self, height=TEXT_HEIGHT, width=TEXT_WIDTH, font=SANS_FONT
        )
        self.output_text.configure(state=DISABLED)
        # self.output_text.bind('<Control-c>', copy_cmd)
        self.output_text.grid(
            row=1, column=2, columnspan=2, sticky=(N, E, W), padx=BORDER, pady=BORDER
        )
        # log rect
        # grid(2, 0-3)
        log_word = self.get_string("log")
        self.logRect = tk.LabelFrame(self, text=log_word, font=MONO_FONT)
        self.logRect.grid(
            row=2, column=0, columnspan=4, sticky=(N, S, E, W), padx=BORDER, pady=BORDER
        )
        self.logRect.grid_rowconfigure(0, weight=2)
        self.logRect.grid_columnconfigure(0, weight=1)
        # log Text
        #self.log_text.textvariable if not first_time else tk.StringVar()
        # self.log_text = FramedVariable(self, var, text=log_word, font=MONO_FONT)
        # self.log_text.grid(
        # row=2, column=0, columnspan=4, sticky=(N, S, E, W), padx=BORDER, pady=BORDER
        # )
        self.log_text = ScrolledText(
            self.logRect,
            #textvariable=self.log_StringVar,
            height=TEXT_HEIGHT // 3,
            width=TEXT_WIDTH * 2,
            bg="black",
            fg=CURSOR_GREEN,
            font=MONO_FONT,
        )
        self.log_text.config(insertbackground="white", state=DISABLED)
        self.log_text.grid(row=0, sticky=(N, S, E, W), padx=BORDER, pady=BORDER)
        # row=2, column=0, columnspan=4,

    def open_preferences(self) -> None:
        # self.prefs_window = openToplevel()
        D = {}
        # D has the following structure:
        # keyword: (current, chosen)
        # keyword is a str like "language" or "tooltip"
        # current is the current value
        # chosen is what the user selected
        cur_section = self.preferences.get_section()
        preferences_word = self.get_string("preferences")
        with CustomToplevel(self, title=preferences_word) as prefs_window:
            # notebook widget
            nb = ttk.Notebook(prefs_window)
            # the notebook will be grided later
            # language tab
            cur_lang = cur_section["language"]
            lang_tab = tk.Frame(nb)
            language_word = self.get_string("language")
            nb.add(lang_tab, text=language_word)
            chosen_lang = tk.StringVar()
            chosen_lang.set(cur_lang)
            D["language"] = (cur_lang, chosen_lang)
            for i, lang in enumerate(sorted(self.language_dict.keys())):
                my_name = self.get_string("my_name", lang=lang)
                rb = tk.Radiobutton(
                    lang_tab, text=my_name, variable=chosen_lang, value=lang
                )
                rb.grid(row=i, column=0, padx=BORDER, pady=BORDER, sticky=(W,))
            # tooltips tab
            cur_tooltip = cur_section.getboolean("tooltip")
            tooltip_tab = tk.Frame(nb)
            tooltip_word = self.get_string("tooltip")
            nb.add(tooltip_tab, text=tooltip_word)
            tooltip_choice = tk.BooleanVar()
            tooltip_choice.set(cur_tooltip)
            D["tooltip"] = (cur_tooltip, tooltip_choice)
            enabled_word = self.get_string(ENABLED)
            cb = tk.Checkbutton(
                tooltip_tab,
                text=enabled_word,
                onvalue=True,
                offvalue=False,
                variable=tooltip_choice,
            )
            cb.grid(row=0, column=0, padx=BORDER, pady=BORDER)  # , sticky=tk.W)
            #
            ok_var = tk.BooleanVar()
            confirm = partial(tk.BooleanVar.set, ok_var, True)
            ok_word = self.get_string("ok")
            ok_button = CustomButton(prefs_window, text=ok_word, command=confirm)
            ok_button.grid(row=1, column=0, padx=BORDER, pady=BORDER)
            restore_word = self.get_string("restore_defaults")
            do_nothing = lambda *args, **kwargs: None
            restore_button = CustomButton(
                prefs_window, text=restore_word, command=do_nothing
            )
            restore_button.grid(row=1, column=1, padx=BORDER, pady=BORDER)
            # center and wait for the user to close the window
            nb.grid(row=0, column=0, columnspan=2, padx=BORDER, pady=BORDER)
            center(prefs_window)
            prefs_window.wait_variable(ok_var)
            # user has closed the window
            proceed = None
            for key, pair in D.items():
                cur, chosen = pair
                chosen = chosen.get()
                if cur == chosen:
                    continue
                # changes.append(f"{k}: {cur} {ARROW} {chosen}")
                if proceed is None:
                    # "is None" ensures that this clause occurs exactly once
                    confirm_changes = self.get_string("confirm_changes")
                    do_you_confirm = self.get_string("do_you_confirm_changes")
                    # body = do_you_confirm_changes + EOL + EOL.join(changes)
                    proceed = self.pop_yesno(do_you_confirm, title=confirm_changes)
                if not proceed:
                    return
                self.preferences.set_user_pref(key, chosen)
                if key == "language":
                    # refreshing the MorlaFrame while it is maximized ("zoomed") is
                    # buggy, for some reason
                    was_zoomed = zoom(self.master)
                    zoom(self.master, False)
                    self.init_menubar()
                    clear_widgets(self)
                    self.init_widgets()
                    if was_zoomed:
                        zoom(self.master, True)
            if proceed:
                self.preferences.save()

    def export2clipboard(self, content, *args) -> None:
        extra = COMMA.join([str(a) for a in args])
        print("extraneous arguments in export2clipboard:", extra)
        self.master.clipboard_clear()
        self.master.clipboard_append(content)

    @property
    def input_text_content(self) -> str:
        return self.input_text.get("1.0", tk.END)

    @divert2log
    def on_open_file(self) -> None:
        open_file_word = self.get_string("open_file")
        filename = filedialog.askopenfilename(
            initialdir=self.last_dir, title=open_file_word, filetypes=self.ftypes
        )
        if filename:
            self.open_file(filename)

    @divert2log
    def open_file(self, filename: str):
        self.last_dir = os.path.dirname(filename)
        # reordering ftypes will only take effect the next time a filename dialog is
        # opened
        ext = get_extension(filename)
        self.reorder_ftypes(ext)
        with open(filename, "r") as f:
            try:
                content = f.read().strip()
            except UnicodeDecodeError:
                msg = f"couldn't read {filename}!"
                print(msg)
                # typeset_Text(msg, self.log_text)
            else:
                typeset_Text(content, self.input_text)

    @divert2log
    def on_save_file(self) -> None:
        save_file_word = self.get_string("save_file")
        filename = filedialog.asksaveasfilename(
            initialdir=self.last_dir, title=save_file_word, filetypes=self.ftypes
        )
        if filename:
            with open(filename, "w") as f:
                f.write(self.input_text_content)
            self.last_dir = os.path.dirname(filename)
            # reordering ftypes will only take effect the next time a filename dialog is
            # opened
            ext = get_extension(filename)
            self.reorder_ftypes(ext)

    def pop_error(self, message) -> None:
        error_word = self.get_string("error")
        with CustomToplevel(self, title=error_word, plain=True) as error_window:
            # error_window = openToplevel(title="Error")
            #
            error_icon = tk.Label(error_window, image=ERROR_SYMBOL)
            error_icon.image = ERROR_SYMBOL
            error_icon.grid(row=0, rowspan=2, column=0, padx=BORDER)
            #
            error_message = tk.Label(error_window, text=message)
            error_message.grid(row=0, column=1)
            #
            # ok_button = tk.Button(error_window, text="Ok", command=error_window.destroy, cursor="hand1")
            # ok_button = CustomButton(error_window, text="Ok", command=error_window.destroy)
            # ok_button.grid(row=1, column=1)
            #
            error_window.bell()
            #
            ok_var = tk.BooleanVar()
            confirm = partial(tk.BooleanVar.set, ok_var, True)
            ok_word = self.get_string("ok")
            ok_button = CustomButton(error_window, text=ok_word, command=confirm)
            ok_button.grid(row=1, column=1)
            #
            center(error_window)
            error_window.wait_variable(ok_var)

    def pop_yesno(self, question: str, title: str = "Question") -> bool:
        with CustomToplevel(self, title=title) as question_window:
            # icon and message
            question_icon = tk.Label(question_window, image=QUESTION_SYMBOL)
            question_icon.image = QUESTION_SYMBOL
            question_icon.grid(row=0, rowspan=2, column=0, padx=BORDER)
            question_message = tk.Label(question_window, text=question)
            question_message.grid(row=0, column=1, columnspan=2)
            # the choice
            choice = tk.BooleanVar()
            choose_yes = partial(tk.BooleanVar.set, choice, True)
            choose_no = partial(tk.BooleanVar.set, choice, False)
            yes_word = self.get_string("yes")
            yes_button = CustomButton(
                question_window, text=yes_word, command=choose_yes
            )
            yes_button.grid(row=1, column=1)
            no_word = self.get_string("no")
            no_button = CustomButton(question_window, text=no_word, command=choose_no)
            no_button.grid(row=1, column=2)
            # center and wait
            center(question_window)
            question_window.wait_variable(choice)
        print(choice.get())
        return choice.get()

    def get_configs_entries(self) -> List[tk.Entry]:
        """Fetchs a list with the Entry widgets at the right side of the
        Configurations window (the "Restore defaults" button is not included).
        """
        # we want the Entry widgets at the right of the config_window, which means
        # column 1 of the grid
        entries = self.config_window.grid_slaves(column=1)
        # the widgets are being counted from bottom to top, so the first widget is not
        # an Entry, but the "Restore defaults" button; we will discard it
        entries = entries[1:]
        # now let's put it into proper order
        entries = entries[::-1]
        return entries

    def typeset_configsEntries(self) -> None:
        """Rewrites the contents of the Entries objects such that they match
        self.configs, which is a Configuration object.
        """
        keys = self.configs.keys()
        entries = self.get_configs_entries()
        for key, entry in zip(keys, entries):
            # value = getattr(self.configs, key)
            value = self.configs[key]
            entry.delete(0, tk.END)
            entry.insert(tk.END, value)

    def open_configs(self):
        configurations_word = self.get_string("configurations")
        self.config_window = open_toplevel(self, title=configurations_word)
        i = 0
        for k, v in self.configs.items():
            label = tk.Label(self.config_window, text=k)
            label_hover = Tooltip(label, f"{i}\n{k}: {v}")
            label.grid(row=i, column=0, sticky=(E,), padx=BORDER)
            # text_var = tk.StringVar(value=v)
            # self.configs_table[k] = text_var
            # text_box = tk.Entry(self.config_window, textvariable=text_var)
            text_box = tk.Entry(self.config_window)
            text_box.insert(tk.END, v)
            text_box.grid(row=i, column=1, sticky=(W,), padx=BORDER)
            #
            i += 1
        i += 1
        # save_changes = tk.Button(self.config_window, text="Save changes", command=self.set_configs, takefocus=0, cursor="hand1", pady=BORDER)
        save_changes_word = self.get_string("save_changes")
        save_changes = CustomButton(
            self.config_window, text=save_changes_word, command=self.set_configs
        )
        save_changes.grid(row=i, column=0)
        # restore_defaults = tk.Button(self.config_window, text="Restore defaults", command=self.restore_configs, takefocus=0, cursor="hand1", pady=BORDER)
        restore_word = self.get_string("restore_defaults")
        restore_defaults = CustomButton(
            self.config_window, text=restore_word, command=self.restore_configs
        )
        restore_defaults.grid(row=i, column=1)
        #
        center(self.config_window)

    def set_configs(self, table: Optional[Configuration] = None):
        if not isinstance(table, Configuration):
            if table is None:
                keys = self.configs.keys()
                entries = self.get_configs_entries()
                D = dict(zip(keys, entries))
                table = Configuration(D)
            else:
                raise ValueError(f"{repr(table)} must be Configuration or None!")
        changes = []
        for k, v in table.items():
            old_v = self.configs[k]
            try:
                new_v = v.get()
            except AttributeError:
                if isinstance(v, str):
                    new_v = v
                else:
                    raise ValueError(f"{repr(v)} must be str or tk.Entry!")
            if old_v != new_v:
                changes.append((k, new_v))
        if not changes:
            # tk.messagebox.showwarning(message="No configurations to change!")
            no_configs_to_change = self.get_string("no_configs_to_change")
            self.pop_error(no_configs_to_change)
            return
        # changes is a list of (str, str); there are no tk objects in changes!
        do_you_confirm_changes = self.get_string("do_you_confirm_changes")
        change_log = [do_you_confirm_changes]
        change_log.extend([f"{k} {ARROW} {v}" for k, v in changes])
        change_log = EOL.join(change_log)
        # can_proceed = tk.messagebox.askyesno(message=change_log)
        confirm_changes = self.get_string("confirm_changes")
        can_proceed = self.pop_yesno(change_log, title=confirm_changes)
        if can_proceed:
            for k, v in changes:
                old_v = self.configs[k]
                print(f"{old_v} {ARROW} {v}")
                self.configs[k] = v
                if self.parser.questions:
                    for q in self.parser.questions:
                        q.configs[k] = v

    def restore_configs(self):
        self.set_configs(table=Configuration())
        self.typeset_configsEntries()

    @divert2log
    def on_parseButton_press(self):
        lines = self.input_text_content.split(EOL)
        self.parser.read(lines, self.configs)
        self.set_exercises_button(True)

    @divert2log
    def on_formatButton_press(self):
        questions = self.parser.pretty_print()
        if questions:
            typeset_Text(questions, self.output_text)
            self.parser.clear(total=True)
            self.set_exercises_button(False)
        else:
            nothing_parsed = self.get_string("no_questions_parsed")
            print(f"{nothing_parsed}.")

    def open_exercises_window(self):
        exercises_word = self.get_string("exercises")
        with CustomToplevel(self, title=exercises_word) as exerc_window:
            pass

    def open_about_window(self):
        name = morla.SELETOR_NAME
        version_word = self.get_string("version", capitalize=False)
        version = ".".join([str(i) for i in morla.SELETOR_VERSION])
        name_str = f"{name}, {version_word} {version}."
        author = morla.SELETOR_AUTHOR
        author_str = self.get_string("author_string") + f" {author}."
        email = morla.SELETOR_EMAIL.replace("<at>", "@")
        # mailto = "mailto:" + email
        # the license is what is enclosed in parenthesis in the license string,
        # excluding the parenthesis
        license = re.findall("\((.+)\)", morla.SELETOR_LICENSE)[0]
        license = f"{COPYRIGHT} {license}"
        logo = self.icon
        # if logo: logo = logo.subsample(7, 7)
        #
        about_word = self.get_string("about")
        window = open_toplevel(self, title=about_word)
        # window.focus_force()
        # with CustomToplevel(self, title="teste") as window:
        # logo
        if logo:
            pic = tk.Label(window, image=logo)
            pic.image = logo
            pic.grid(row=0, rowspan=4, column=0, padx=BORDER)
        # name
        name_label = tk.Label(window, text=name_str)
        name_label.grid(row=0, column=1)
        # author
        author_label = tk.Label(window, text=author_str)
        author_label.grid(row=1, column=1)
        # email
        email_Label = tk.Label(
            window, text=email, justify="center", relief=RAISED, padx=BORDER
        )
        email_Label.grid(row=2, column=1)
        # TOP = email_Label.winfo_toplevel()
        email_export = partial(self.export2clipboard, email)
        email_copy = self.get_string("email_copy")
        email_hoverinfo = Tooltip(email_Label, email_copy)
        email_Label.bind("<Any-Button>", email_export)
        # license information
        license_label = tk.Label(window, text=license)
        license_label.grid(row=3, column=1)
        #
        center(window)


def _cleanup() -> None:
    with Cd(morla_frame.full_app_dir):
        ini_name = "preferences.ini"
        try:
            os.remove(ini_name)
            # os.rmdir(morla_frame.full_app_dir)
        except FileNotFoundError:
            print("Couldn't erase", ini_name)
        else:
            print(f"File {ini_name} erased.")
        with Cd(morla_frame.home_dir):
            try:
                os.rmdir(".morla")
            except FileNotFoundError:
                print("Couldn't erase .morla")
            else:
                print(f"Directory {morla_frame.home_dir}.morla/ erased.")


def gui_loop() -> None:
    to_open = sys.argv[1] if len(sys.argv) == 2 else ""
    morla_frame = MorlaFrame(to_open)
    exit_status = morla_frame.mainloop()
    if False:
        _cleanup()
    sys.exit(exit_status)


if __name__ == "__main__":
    sys.exit("This module should not be run alone.")
