import base64
import binascii
import json
import os
import time
import socket
import threading
from tkinter import *
from tkinter import messagebox
from cryptography.fernet import Fernet, InvalidToken
from random import randint, choice


class CampeonatoTabuada:
    def __init__(self, root):
        self.root = root
        self.root.title("Campeonato de Tabuada")
        self.root.attributes("-fullscreen", True)
        self.root.config(bg="#ffffff")

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        self.title_font_size = int(self.screen_height * 0.05)
        self.button_font_size = int(self.screen_height * 0.03)

        self.players = []
        self.num_players = 0
        self.current_player_index = 0
        self.current_round = 0
        self.current_player = None
        self.multiplicand = None
        self.multiplier = None

        self.max_rounds_per_player = 3

        self.scores = {}
        self.key = self.generate_key()
        self.load_scores()  # Carregar os scores do arquivo JSON
        self.load_settings()  # Carregar as configurações do jogo
        self.time_limit = 5  # Tempo limite em segundos

        # Configuração do socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((socket.gethostname(), 12345))
        self.server_socket.listen(5)
        self.client_socket = None

        if self.scores:  # Se houver scores salvos, ir para a tela do jogo diretamente
            self.load_players_from_scores()
            self.create_widgets()
            self.wait_for_client_connection()
        else:
            self.create_start_screen()

    def load_players_from_scores(self):
        self.players = list(self.scores.keys())
        self.num_players = len(self.players)

    def save_settings(self):
        settings = {"total_tabuadas": self.total_tb_multi}
        try:
            with open("settings.json", "w") as file:
                json.dump(settings, file)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar as configurações: {str(e)}")

    def load_settings(self):
        try:
            with open("settings.json", "r") as file:
                settings = json.load(file)
                self.total_tb_multi = settings.get("total_tabuadas", 10)
        except FileNotFoundError:
            self.total_tb_multi = 10

    def generate_key(self):
        # Gerar chave se não existir
        key_path = "key.key"
        if not os.path.exists(key_path):
            key = Fernet.generate_key()
            with open(key_path, "wb") as key_file:
                key_file.write(key)
        else:
            with open(key_path, "rb") as key_file:
                key = key_file.read()
        return key

    def encrypt_data(self, data, key):
        cipher_suite = Fernet(key)
        encrypted_data = cipher_suite.encrypt(data.encode())
        return encrypted_data

    def decrypt_data(self, encrypted_data, key):
        cipher_suite = Fernet(key)
        decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
        return decrypted_data

    def load_scores(self):
        scores_path = "score.json"
        if os.path.exists(scores_path):
            try:
                with open(scores_path, "rb") as file:
                    encrypted_data = file.read()
                    self.scores = json.loads(
                        self.decrypt_data(encrypted_data, self.key)
                    )
            except (
                FileNotFoundError,
                InvalidToken,
                binascii.Error,
                json.JSONDecodeError,
            ) as e:
                messagebox.showerror("Erro", f"Erro ao carregar os scores: {str(e)}")
                self.scores = {}

    def save_scores(self):
        scores_path = "score.json"
        try:
            with open(scores_path, "wb") as file:
                encrypted_data = self.encrypt_data(json.dumps(self.scores), self.key)
                file.write(encrypted_data)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar os scores: {str(e)}")

    def create_start_screen(self):
        self.start_label = Label(
            self.root,
            text="Insira os nomes dos alunos (separados por vírgula):",
            font=("Arial", int(self.screen_height * 0.025)),
            bg="#ffffff",
            fg="#000000",
        )

        self.start_label.pack()

        self.player_entry = Entry(
            self.root,
            font=("Arial", int(self.screen_height * 0.02)),
            bg="#ffffff",
            fg="#000000",
        )
        self.player_entry.pack()

        self.multi_label = Label(
            self.root,
            text="Insira a quantidade de tabuadas:",
            font=("Arial", int(self.screen_height * 0.025)),
            bg="#ffffff",
            fg="#000000",
        )

        self.multi_label.pack()

        self.multi_entry = Entry(
            self.root,
            font=("Arial", int(self.screen_height * 0.02)),
            bg="#ffffff",
            fg="#000000",
        )

        self.multi_entry.pack()

        self.start_button = Button(
            self.root,
            text="Iniciar",
            font=("Arial", int(self.screen_height * 0.025)),
            command=self.start_game,
        )
        self.start_button.pack(pady=self.screen_height * 0.02)

        # Carregar as configurações existentes, se disponíveis
        self.multi_entry.insert(0, str(self.total_tb_multi))

        # Gerar chave de criptografia
        self.key = self.generate_key()

    def start_game(self):
        players_input = self.player_entry.get().strip()
        self.players = [name.strip() for name in players_input.split(",")]

        self.total_tb_multi = (
            int(self.multi_entry.get()) if self.multi_entry.get() != "" else 10
        )

        self.save_settings()  # Salvar as configurações do jogo
        self.num_players = len(self.players)
        if self.num_players < 2:
            messagebox.showerror(
                "Erro", "É necessário inserir pelo menos dois nomes de alunos."
            )
            return
        for player in self.players:
            if player not in self.scores:
                self.scores[player] = 0
        self.start_label.pack_forget()
        self.player_entry.pack_forget()
        self.start_button.pack_forget()
        self.multi_label.pack_forget()
        self.multi_entry.pack_forget()
        self.create_widgets()
        self.wait_for_client_connection()

    def create_widgets(self):
        self.title_label = Label(
            self.root,
            text="Campeonato de Tabuada",
            font=("Arial", self.title_font_size, "bold"),
            bg="#ffffff",
            fg="#000000",
        )
        self.title_label.pack(
            pady=(self.screen_height * 0.1, self.screen_height * 0.02)
        )

        self.student_label = Label(
            self.root,
            text="Aluno Atual: ",
            font=("Arial", int(self.screen_height * 0.025)),
            bg="#ffffff",
            fg="#000000",
        )
        self.student_label.pack()

        self.random_button = Button(
            self.root,
            text="Escolher Aluno Aleatoriamente",
            font=("Arial", int(self.screen_height * 0.025)),
            command=self.select_random_student,
        )
        self.random_button.pack(pady=self.screen_height * 0.02)

        self.question_label = Label(
            self.root,
            text="",
            font=("Arial", self.title_font_size),
            bg="#ffffff",
            fg="#000000",
        )
        self.question_label.pack()

        self.answer_label = Label(
            self.root,
            text="",
            font=("Arial", self.title_font_size),
            bg="#ffffff",
            fg="#000000",
        )
        self.answer_label.pack()

        self.button_frame = Frame(self.root, bg="#ffffff")
        self.button_frame.pack()

        self.score_button = Button(
            self.button_frame,
            text="Acertou",
            font=("Arial", int(self.screen_height * 0.025)),
            command=self.score_student,
            state=DISABLED,
        )
        self.score_button.pack(side=LEFT, padx=(0, self.screen_width * 0.02))

        self.skip_button = Button(
            self.button_frame,
            text="Errou",
            font=("Arial", int(self.screen_height * 0.025)),
            command=self.skip_player,
            state=DISABLED,
        )
        self.skip_button.pack(side=LEFT)

        self.leaderboard_button = Button(
            self.root,
            text="Quadro de Líderes",
            font=("Arial", int(self.screen_height * 0.025)),
            command=self.show_leaderboard,
        )
        self.leaderboard_button.pack(pady=self.screen_height * 0.02)

        self.score_table = Frame(
            self.root,
            bg="#ffffff",
        )
        self.score_table.pack()

        self.player_labels = []
        self.score_labels = []

        for i, player in enumerate(self.players):
            player_label = Label(
                self.score_table,
                text=player,
                font=("Arial", int(self.screen_height * 0.02)),
                bg="#ffffff",
                fg="#000000",
            )
            player_label.grid(row=i, column=0, padx=(0, self.screen_width * 0.02))
            self.player_labels.append(player_label)

            score_label = Label(
                self.score_table,
                text=str(self.scores[player]),
                font=("Arial", int(self.screen_height * 0.02)),
                bg="#ffffff",
                fg="#000000",
            )
            score_label.grid(row=i, column=1)
            self.score_labels.append(score_label)

        # Iniciar a thread para escutar o cliente
        self.listen_thread = threading.Thread(target=self.listen_to_client)
        self.listen_thread.daemon = True  # Definir a thread como um daemon para que ela seja encerrada quando a aplicação principal for encerrada
        self.listen_thread.start()

    def wait_for_client_connection(self):
        self.client_socket, addr = self.server_socket.accept()
        self.select_random_student()

    def listen_to_client(self):
        try:
            while True:
                if self.client_socket is not None:
                    data = self.client_socket.recv(1024).decode()
                    if not data:
                        break

                    print("Mensagem do cliente:", data)
                    messagebox.showinfo("Resposta da(o) aluna(o)", data)
        except Exception as e:
            print("Erro ao escutar o cliente:", e)

    def select_random_student(self):
        if self.num_players > 0:
            self.current_player_index = randint(0, self.num_players - 1)
            current_player = self.players[self.current_player_index]
            self.student_label.config(text=f"Aluno Atual: {current_player}")
            self.generate_question()
            self.score_button.config(state=NORMAL)
            self.skip_button.config(state=NORMAL)
            self.send_question_to_client(
                self.multiplicand,
                self.multiplier,
                self.correct_answer,
                teacher_response="",
                student_play=current_player,
            )

    def generate_question(self):
        if self.num_players == 0:
            return
        current_player = self.players[self.current_player_index]
        self.current_player = current_player
        self.multiplicand = randint(1, 10)
        self.multiplier = randint(1, 10)
        self.correct_answer = self.multiplicand * self.multiplier
        self.question_label.config(
            text=f"{current_player}, quanto é {self.multiplicand} x {self.multiplier}?"
        )
        self.answer_label.config(text=f"Resposta: {self.correct_answer}")

        self.send_question_to_client(
            self.multiplicand,
            self.multiplier,
            self.correct_answer,
            teacher_response="",
            student_play=self.current_player,
        )

    def send_question_to_client(
        self,
        multiplicand,
        multiplier,
        correct_answer,
        teacher_response="",
        student_play="",
    ):
        question_data = {
            "multiplicand": multiplicand,
            "multiplier": multiplier,
            "correct_answer": correct_answer,
            "time_limit": self.time_limit,
            "_teacher_response": teacher_response,
            "_student_play": student_play,
        }
        self.client_socket.sendall((json.dumps(question_data) + "\n").encode())

    def score_student(self):
        current_player = self.players[self.current_player_index]
        self.scores[current_player] += 1
        self.update_score_table()
        self.next_round()
        self.send_question_to_client(
            self.multiplicand,
            self.multiplier,
            self.correct_answer,
            teacher_response="Acertou!",
            student_play=self.current_player,
        )

    def skip_player(self):
        self.next_round()
        self.send_question_to_client(
            self.multiplicand,
            self.multiplier,
            self.correct_answer,
            teacher_response="Errou!",
            student_play=self.current_player,
        )

    def update_score_table(self):
        for i, player in enumerate(self.players):
            self.score_labels[i].config(text=str(self.scores[player]))
        self.save_scores()

    def next_round(self):
        self.score_button.config(state=DISABLED)
        self.skip_button.config(state=DISABLED)
        self.current_round += 1
        if self.current_round < self.num_players * self.max_rounds_per_player:
            self.select_random_student()
        else:
            self.end_game()

    def show_leaderboard(self):
        leaderboard_text = "Quadro de Líderes:\n"
        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        for player, score in sorted_scores:
            leaderboard_text += f"{player}: {score}\n"
        messagebox.showinfo("Quadro de Líderes", leaderboard_text)

    def end_game(self):
        self.show_leaderboard()
        self.root.destroy()


if __name__ == "__main__":
    root = Tk()
    app = CampeonatoTabuada(root)
    root.mainloop()
