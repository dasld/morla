# -*- coding: utf-8 -*-

from typing import Optional, Union

# tk provides the re module
from tkinter import re

from morla.configuration import Configuration
from morla.utils import *


class Question:
    CHOICES_TYPE = "choices question"
    WRITTEN_TYPE = "written question"
    TYPES = (CHOICES_TYPE, WRITTEN_TYPE)

    def __init__(
        self,
        source: str,
        year: str,
        question_type: str,
        answer: Optional[str],
        histories: list,
        tags: list,
        texts: list,
        choices: list,
        wrongs: list,
        explanations: list,
        configs: Optional[Union[dict, Configuration]] = None,
    ) -> None:
        # configs
        self.configs = Configuration(configs)
        # source
        if isinstance(source, str):
            self.source = source
        else:
            raise ValueError("source must be str!")
        # year
        if year.isdigit() or year == self.configs.BAD_YEAR:
            self.year = year
        else:
            raise ValueError(f"{repr(year)} must be int or {self.configs.BAD_YEAR}!")
        # question_type
        if question_type in self.TYPES:
            self.question_type = question_type
        else:
            raise ValueError(f"{repr(question_type)} is not a valid question type!")
        assert not (question_type == self.WRITTEN_TYPE and answer)
        # answer
        if isinstance(answer, str):
            self.answer = answer
        else:
            raise ValueError(f"{repr(answer)} must be str!")
        # lists
        for arg in (histories, tags, texts, choices, wrongs, explanations):
            if not isinstance(arg, list):
                raise ValueError(f"{repr(arg)} must be list!")
        self.histories = histories
        self.tags = tags
        self.texts = texts
        self.choices = choices
        self.wrongs = wrongs
        self.explanations = explanations

    def __repr__(self):
        body = SPACE.join(self.texts)
        return truncate(body, 15)

    def __str__(self):
        configs = self.configs
        print(truncate(str(configs), prefix=f"{repr(self)} settings: "))
        # start of the question body
        body = [configs.BEGIN_QUESTION]
        body.extend(self.texts)
        # insert choices, if there are any
        if self.question_type == self.CHOICES_TYPE:
            body.append(configs.BEGIN_CHOICES)
            for c in self.choices:
                if c == self.answer:
                    label = configs.CORRECT
                else:
                    label = configs.CHOICE
                body.append(f"{label} {c}")
            body.append(configs.END_CHOICES)
        # finish the body
        body.append(configs.END_QUESTION)
        # the explanations
        explanation = [configs.BEGIN_ANSWER]
        explanation.extend(self.explanations)
        explanation.append(configs.END_ANSWER)
        # assemble and return
        body = EOL.join(body)
        explanation = EOL.join(explanation)
        return f"{body}{EOL}{explanation}"


class Parser:
    IN_QUESTION = "in question"
    IN_ANSWER = "in answer"
    OUT = "out"
    # the following pattern matches words linked by an = sign
    # (sided or not by spaces). Colons : may appear in the second word only.
    # The second word might be enclosed in curly braces.
    # >>> Parser.pattern.findall("[foo=bar, baz = b:azz]")
    # ... [("foo", "bar"), ("baz", "b:azz")]
    # many str with no comma in between are automatically concatenated, so the
    # following will be a single str
    pattern = re.compile(
        r"[\s\[,]{0,2}"  # 0, 1 or 2 whitespaces or [ or ,
        r"([\w\-]+)"  # 1st group: a word (with or without hyphens)
        r"\s*"  # optional whitespace
        "="  # the = character
        r"\s*"  # optional whitespace
        r"({?[\w:\-]+}?)"  # 2nd group: a word (with or without hyphens and
        # colons and enclosed or not in curly braces)
        r"\]?"  # optional ]
    )

    def __init__(self) -> None:
        self.location = None
        # strings
        self.source = ""
        self.year = ""
        self.question_type = ""
        self.answer = ""
        # lists
        self.histories = []
        self.tags = []
        self.texts = []
        self.choices = []
        self.wrongs = []
        self.explanations = []
        self.dynamic = (
            self.histories,
            self.tags,
            self.texts,
            self.choices,
            self.wrongs,
            self.explanations,
        )
        # the questions list
        self.questions = []

    def clear(self, total=False):
        self.source = ""
        self.year = ""
        self.question_type = ""
        self.answer = ""
        for L in self.dynamic:
            L.clear()
        if total:
            self.questions.clear()

    def get_question(self, configs: Optional[Union[dict, Configuration]]) -> Question:
        copies = [L[:] for L in self.dynamic]
        q = Question(
            self.source,
            self.year,
            self.question_type,
            self.answer,
            *copies,
            configs=configs,
        )
        self.clear()
        return q

    def read(self, text: list, configuration: Union[dict, Configuration]) -> None:
        if isinstance(configuration, (dict, Configuration)):
            configs = Configuration(configuration)
        else:
            raise ValueError(f"{repr(configuration)} must be dict or Configuration!")
        # configs is necessarily a Configuration instance
        self.location = self.OUT
        sample = SPACE.join(text[:6])
        print(truncate(sample, prefix="Reading: "))
        for index, line in enumerate(text):
            line = line.strip()
            print(truncate(line, prefix=f"{index}: "))
            if line.startswith(PERCENT):
                # the current line is a LaTeX comment
                # first, disregard the % character
                line = delete(line, PERCENT)
                if self.location == self.OUT:
                    # a question has started! reset the question_type:
                    self.question_type = ""
                    # position the reader correctly:
                    self.location = self.IN_QUESTION
                    # parse this first line; it should be in the
                    # % UFRJ-RJ 2011
                    # format
                    tokens = line.split()
                    self.source = SPACE.join(tokens[:-1])
                    self.year = tokens[-1]
                elif line.startswith(configs.USO):
                    # the current line is a
                    # % Uso: lista01-19, aula13-19
                    # line
                    line = delete(line, configs.USO)
                    tokens = line.split(COMMA)
                    self.histories.extend(tokens)
                elif line.startswith(configs.TAGS):
                    # the current line is a
                    # % Tags: figuras de linguagem, sintaxe
                    # line
                    line = delete(line, configs.TAGS)
                    tokens = [t.strip() for t in line.split(",")]
                    self.tags.extend(tokens)
            elif line.startswith(configs.BEGIN_QUESTION):
                # the current line is a
                # \begin{Exercise}[label=ufa,origin={UFA-AM}]
                # line
                for latex_key, latex_value in self.pattern.findall(line):
                    latex_key = latex_key.lower()
                    latex_value = latex_value.lower()
                    source = self.source.lower()
                    if latex_key == configs.LABEL:
                        if latex_value.strip("q:") not in source:
                            print(f"{latex_value} is not in {self.source}!")
                        else:
                            pass
                            # print(f"{latex_key}={latex_value} is ok!")
                    elif latex_key == configs.ORIGIN:
                        if latex_value.strip("}{") not in self.source:
                            print(f"{latex_value} is not in {self.source}!")
                        else:
                            pass
                            # print(f"{latex_key}={latex_value} is ok!")
            elif line.startswith(configs.BEGIN_CHOICES):
                # this question is a choices question
                self.question_type = Question.CHOICES_TYPE
            elif line.startswith(configs.CHOICE):
                # this line contains a choice:
                # \choice fática.
                assert self.question_type == Question.CHOICES_TYPE
                line = delete(line, configs.CHOICE)
                self.choices.append(line)
            elif line.startswith(configs.CORRECT):
                # this line contains the correct choice:
                # \CorrectChoice fática.
                assert self.question_type == Question.CHOICES_TYPE
                line = delete(line, configs.CORRECT)
                self.answer = line
                self.choices.append(line)
            elif line.startswith(configs.END_CHOICES):
                # this is the \end{choices} line
                self.wrongs.extend(self.choices)
                self.wrongs.remove(self.answer)
            elif line.startswith(configs.END_QUESTION):
                # this is the \end{Exercise} line
                assert self.location == self.IN_QUESTION
                self.location = self.OUT
                if not self.question_type:
                    self.question_type = Question.WRITTEN_TYPE
            elif line.startswith(configs.BEGIN_ANSWER):
                assert self.location == self.OUT
                self.location = self.IN_ANSWER
            elif line.startswith(configs.END_ANSWER):
                assert self.location == self.IN_ANSWER
                q = self.get_question(configs)
                self.questions.append(q)
                print("Nova questão:")
                print(q)
                print(truncate(str(self.questions), prefix="self.questions: "))
                self.location = self.OUT
            elif line:
                # the line is plain text; append it in the proper list:
                if self.location == self.IN_QUESTION:
                    self.texts.append(line)
                elif self.location == self.IN_ANSWER:
                    self.explanations.append(line)
                else:
                    # something wrong has happened
                    pass
            # print(reveal(self))
        self.location = None

    def pretty_print(self) -> str:
        if not self.questions:
            # no_questions_parsed = self.gets
            print("No questions have been correctly parsed.")
            return ""
        double_eol = EOL * 2
        return double_eol.join([str(q) for q in self.questions])

    def __str__(self) -> str:
        """Prints the first three parsed questions, truncated.
        """
        sample_questions = self.questions[:3]
        sample_text = COMMA.join(sample_questions)
        return truncate(sample_text, prefix="Questões: ")


if __name__ == "__main__":
    print("This module should not be run alone.")
    from tkinter import sys

    sys.exit()
