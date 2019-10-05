from typing import Union, Optional
import tkinter as tk
from PIL import Image, ImageTk
import base64
import io

txt_path = "/home/daniel/Documents/Informática/git/morla/logo.txt"
gif_path = txt_path.replace("txt", "gif")

#with open(gif_path, "rb") as gif:
#    b = gif.read()
#    b64 = base64.b64encode(b)
#    data = io.BytesIO(b64)
    #data = io.BytesIO()
    #for line in txt:
    #    data.write(line.strip().encode())
    #string = data.getvalue().decode("utf-8")

def bin_as_b64txt(binary_path: str, txt_path: str) -> None:
    """Saves a binary file as a base64-encoded UTF-8 text file. A newline
    character (b'\n') is inserted after every 76 bytes of the output, and the
    output is ensured to end with a newline, as per RFC 2045 (MIME).
    https://tools.ietf.org/html/rfc2045.html
    :param str binary_path: the path to the binary file to be read.
    :param str txt_path: the path to the txt file to be written.
    """
    with open(binary_path, "rb") as binary, open(txt_path, 'w') as txt:
        data = io.BytesIO()
        base64.encode(binary, data)
        # decode is a method of the bytes built-in class that converts a bytes
        # object into a string. The default encoding is "utf-8".
        txt.write(data.getvalue().decode())

def txt2bin(txt_path: str,
            binary_path: Optional[str] = None,
            mode: Optional[str] = "base64") \
            -> Optional[io.BytesIO]:
    """Loads an UTF-8-encoded text file containing base64-bytes and return a
    io.BytesIO object with normal bytes.
    :param str txt_path: the path to the txt file to be written.
    :param str binary_path: the path to the binary file to be written.
    :return: io.BytesIO with non-base64 bytes
    """
    if isinstance(mode, str):
        if mode not in ("normal", "base64"):
            message = f"mode must be 'normal' or 'base64'."
            raise ValueError(message)
    else:
        message = f"mode must be 'normal' or 'base64'; {type(mode)} found."
        raise TypeError(message)
    #
    with open(txt_path, 'r') as txt:
        # encode is a method of the built-in class str that encodes a string
        # as a bytes object. The default encoding is "utf-8".
        b = txt.read().strip().encode()
        if mode == "base64":
            b = base64.b64decode(b)
        try:
            with open(binary_path, "wb") as binary:
                binary.write(b)
        except TypeError as err:
            if binary_path is None:
                return io.BytesIO(b)
            message = f"binary_path must be str or None;\
                        {type(binary_path)} found."
            message = tk.re.sub("\s{2,}", ' ', message)
            raise err(message)
        except OSError:
            message = f"binary_path must be str or None;\
                        {type(binary_path)} found."
            message = tk.re.sub("\s{2,}", ' ', message)
            print(message)
            raise

bin_as_b64txt(gif_path, txt_path)
data = txt2bin(txt_path)
print(data.getvalue()[:76])
#img = Image.frombytes("RGBA", (96,96), data.getvalue(), 'raw')

#raw_image = data.getvalue()
#print(string[:76], type(string))
#print()

#with io.StringIO() as t:
#    base64.decode(data, t)
#    print(t.getvalue(), type(t))
#img = Image.frombytes('RGBA', (96,96), raw_image, 'raw')
#img = Image.open(data)

#r = tk.Tk()
#pic = tk.Label(r, image=raw_image)
#pic.image = raw_image
#pic.grid()


#with open("dump.txt", "wb") as dump:
#    dump.write(ascii_gif)

#binary_logo = binascii.unhexlify(hexadecimal_logo)
#with open("dump.gif", "wb") as gif:
#    gif.write(binary_logo)
