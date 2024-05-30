import json
import socket
from tkinter import *
from tkinter import messagebox
import threading


class ClienteTabuada:
    def __init__(self, root):
        self.root = root
        self.root.title("Jogo da Tabuada")
        self.root.attributes("-fullscreen", True)
        self.root.config(bg="#ffffff")

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        self.question_data = {}
        self.answer = None
        self.server_socket = None

        self.create_widgets()
        self.connect_to_server()

        # Inicia uma thread para escutar as mudanças do servidor
        self.listen_thread = threading.Thread(target=self.listen_server)
        self.listen_thread.daemon = True
        self.listen_thread.start()

    def create_widgets(self):
        self.question_label = Label(
            self.root,
            text="",
            font=("Arial", int(self.screen_height * 0.05)),
            bg="#ffffff",
            fg="#000000",
        )
        self.question_label.pack(pady=self.screen_height * 0.2)

        self.answer_entry = Entry(
            self.root,
            font=("Arial", int(self.screen_height * 0.05)),
            bg="#ffffff",
            fg="#000000",
        )
        self.answer_entry.pack()

        self.send_button = Button(
            self.root,
            text="Enviar",
            font=("Arial", int(self.screen_height * 0.05)),
            bg="#ffffff",
            fg="#000000",
            command=self.send_answer,
        )
        self.send_button.pack(pady=self.screen_height * 0.02)

        self.status_label = Label(
            self.root,
            text="",
            font=("Arial", int(self.screen_height * 0.05)),
            bg="#ffffff",
            fg="#000000",
        )
        self.status_label.pack()

    def connect_to_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect(("127.0.0.1", 12345))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao conectar ao servidor: {str(e)}")
            self.root.destroy()

    def listen_server(self):
        buffer = ""
        try:
            while True:
                data = self.server_socket.recv(1024).decode()
                if data:
                    buffer += data
                    while "\n" in buffer:
                        message, buffer = buffer.split("\n", 1)
                        if message:
                            self.question_data = json.loads(message)
                            self.root.after(0, self.update_question)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao escutar o servidor: {str(e)}")
            self.root.destroy()

    def update_question(self):
        multiplicand = self.question_data["multiplicand"]
        multiplier = self.question_data["multiplier"]
        teacher_response = self.question_data.get("_teacher_response", "")
        student_play = self.question_data.get("_student_play", "")

        if teacher_response:
            print(teacher_response)  # Manter o print para depuração
            self.status_label.config(text=teacher_response)

        self.question_label.config(
            text=f"{student_play}, quanto é {multiplicand} x {multiplier}?"
        )

    def send_answer(self):
        try:
            self.answer = int(self.answer_entry.get())
            self.server_socket.sendall((str(self.answer) + "\n").encode())
            self.answer_entry.delete(0, END)
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira apenas números.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao enviar a resposta: {str(e)}")
            self.root.destroy()


if __name__ == "__main__":
    root = Tk()
    app = ClienteTabuada(root)
    root.mainloop()
