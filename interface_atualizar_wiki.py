import customtkinter as ctk
import subprocess
import threading
import os
import glob

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class WikiApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Atualizador de Wiki")
        self.geometry("500x300")

        # Label de status
        self.label_status = ctk.CTkLabel(self, text="Clique em um botão abaixo para iniciar.", wraplength=480)
        self.label_status.pack(pady=20)

        # 🔼 Botão Buscar atualizações primeiro
        self.botao_buscar = ctk.CTkButton(self, text="Buscar atualizações", command=self.buscar_atualizacoes)
        self.botao_buscar.pack(pady=10)

        # 🔽 Botão Atualizar Wiki com confirmação
        self.botao_atualizar = ctk.CTkButton(self, text="Atualizar Wiki (Textos + Imagens)", command=self.confirmar_atualizacao)
        self.botao_atualizar.pack(pady=10)

        # Barra de progresso
        self.progress_bar = ctk.CTkProgressBar(self, width=300)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10)

    # Função para confirmar antes de atualizar tudo
    def confirmar_atualizacao(self):
        confirm = ctk.CTkToplevel(self)
        confirm.title("Confirmação")
        confirm.geometry("400x150")
        confirm.grab_set()

        msg = ctk.CTkLabel(confirm, text="Tem certeza que deseja baixar textos, imagens e unificar tudo?", wraplength=380)
        msg.pack(pady=20)

        botoes = ctk.CTkFrame(confirm)
        botoes.pack()

        btn_sim = ctk.CTkButton(botoes, text="Sim", command=lambda: [confirm.destroy(), self.iniciar_atualizacao()])
        btn_sim.pack(side="left", padx=10)

        btn_nao = ctk.CTkButton(botoes, text="Cancelar", command=confirm.destroy)
        btn_nao.pack(side="left", padx=10)

    def iniciar_atualizacao(self):
        self.botao_atualizar.configure(state="disabled")
        self.botao_buscar.configure(state="disabled")
        self.label_status.configure(text="Iniciando atualização completa...")
        self.progress_bar.set(0.1)
        threading.Thread(target=self.executar_scripts).start()

    def executar_scripts(self):
        try:
            self.label_status.configure(text="Extraindo textos da Wiki...")
            subprocess.run(["python", "textos.py"], check=True)
            self.progress_bar.set(0.33)

            self.label_status.configure(text="Baixando imagens da Wiki...")
            subprocess.run(["python", "fotos.py"], check=True)
            self.progress_bar.set(0.66)

            self.label_status.configure(text="Unificando textos e imagens...")
            subprocess.run(["python", "unificado.py"], check=True)
            self.progress_bar.set(1.0)

            status_final = self.ler_ultimo_status()
            self.label_status.configure(text=status_final)

        except subprocess.CalledProcessError as e:
            self.label_status.configure(text=f"❌ Erro durante execução: {e}")
        finally:
            self.botao_atualizar.configure(state="normal")
            self.botao_buscar.configure(state="normal")

    def buscar_atualizacoes(self):
        self.botao_buscar.configure(state="disabled")
        self.botao_atualizar.configure(state="disabled")
        self.label_status.configure(text="Buscando novas wikis...")
        self.progress_bar.set(0.2)
        threading.Thread(target=self.executar_busca).start()

    def executar_busca(self):
        try:
            subprocess.run(["python", "textos.py"], check=True)
            self.progress_bar.set(1.0)

            status = self.ler_ultimo_status()
            self.label_status.configure(text=status)
        except subprocess.CalledProcessError as e:
            self.label_status.configure(text=f"❌ Erro ao buscar atualizações: {e}")
        finally:
            self.botao_buscar.configure(state="normal")
            self.botao_atualizar.configure(state="normal")

    def ler_ultimo_status(self):
        arquivos_log = sorted(glob.glob("log/status_atualizacao_*.txt"), reverse=True)
        if arquivos_log:
            with open(arquivos_log[0], "r", encoding="utf-8") as f:
                return f.read()
        return "✅ Busca finalizada, mas nenhum log encontrado."


if __name__ == "__main__":
    app = WikiApp()
    app.mainloop()
