import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
                             QLabel, QMessageBox, QListWidget, QListWidgetItem)
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtCore import Qt


class DatabaseManager:
    """Gère les opérations de base de données."""

    @staticmethod
    def create_connection():
        """Crée une connexion à la base de données SQLite."""
        db = QSqlDatabase.addDatabase("QSQLITE")
        db.setDatabaseName("cornell_notes.db")
        if not db.open():
            print("Impossible de se connecter à la base de données")
            return False
        return True

    @staticmethod
    def create_table():
        """Crée la table 'notes' avec la nouvelle structure si elle n'existe pas."""
        query = QSqlQuery()
        query.exec("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            contenu TEXT,
            resume TEXT,
            rappel TEXT,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

    @staticmethod
    def init_db():
        """Initialise la base de données."""
        if not DatabaseManager.create_connection():
            return False
        DatabaseManager.create_table()
        return True


class CornellNotesApp(QMainWindow):
    """Application principale pour la prise de notes Cornell."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cornell Notes")
        self.setGeometry(100, 100, 1000, 600)
        self.setup_ui()
        self.clear_fields()

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Zone de liste des notes
        notes_list_layout = QVBoxLayout()
        self.notes_list = QListWidget()
        self.notes_list.itemClicked.connect(self.load_note)
        notes_list_layout.addWidget(QLabel("Notes existantes:"))
        notes_list_layout.addWidget(self.notes_list)
        main_layout.addLayout(notes_list_layout)

        # Zone de prise de notes
        note_layout = QVBoxLayout()

        # Titre
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Entrez le titre de la note")
        note_layout.addWidget(self.title_input)

        # Zone principale de notes
        main_note_layout = QHBoxLayout()

        # Colonne de rappel
        self.cue_column = QTextEdit()
        self.cue_column.setPlaceholderText("Rappel")
        main_note_layout.addWidget(self.cue_column, 1)

        # Notes principales
        self.main_notes = QTextEdit()
        self.main_notes.setPlaceholderText("Contenu")
        main_note_layout.addWidget(self.main_notes, 3)

        note_layout.addLayout(main_note_layout)

        # Résumé
        self.summary = QTextEdit()
        self.summary.setPlaceholderText("Résumé")
        note_layout.addWidget(self.summary)

        # Boutons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Sauvegarder")
        self.save_button.clicked.connect(self.save_note)
        self.new_button = QPushButton("Nouvelle note")
        self.new_button.clicked.connect(self.clear_fields)
        self.delete_button = QPushButton("Supprimer")
        self.delete_button.clicked.connect(self.delete_note)
        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.delete_button)
        note_layout.addLayout(button_layout)

        main_layout.addLayout(note_layout, 3)

        self.load_notes_list()

    def save_note(self):
        """Sauvegarde la note actuelle dans la base de données."""
        titre = self.title_input.text()
        rappel = self.cue_column.toPlainText()
        contenu = self.main_notes.toPlainText()
        resume = self.summary.toPlainText()

        if not titre:
            QMessageBox.warning(self, "Erreur", "Le titre ne peut pas être vide.")
            return

        query = QSqlQuery()
        if self.notes_list.currentItem() and self.notes_list.currentItem().data(Qt.ItemDataRole.UserRole):
            # Mise à jour d'une note existante
            note_id = self.notes_list.currentItem().data(Qt.ItemDataRole.UserRole)
            query.prepare("""
            UPDATE notes SET titre = ?, contenu = ?, resume = ?, rappel = ?
            WHERE id = ?
            """)
            query.addBindValue(titre)
            query.addBindValue(contenu)
            query.addBindValue(resume)
            query.addBindValue(rappel)
            query.addBindValue(note_id)
        else:
            # Création d'une nouvelle note
            query.prepare("""
            INSERT INTO notes (titre, contenu, resume, rappel)
            VALUES (?, ?, ?, ?)
            """)
            query.addBindValue(titre)
            query.addBindValue(contenu)
            query.addBindValue(resume)
            query.addBindValue(rappel)

        if query.exec():
            QMessageBox.information(self, "Succès", "Note sauvegardée avec succès")
            self.load_notes_list()
            self.clear_fields()
        else:
            QMessageBox.critical(self, "Erreur", "Erreur lors de la sauvegarde de la note")

    def load_notes_list(self):
        """Charge la liste des notes depuis la base de données."""
        self.notes_list.clear()
        query = QSqlQuery("SELECT id, titre FROM notes ORDER BY date_creation DESC")
        while query.next():
            note_id = query.value(0)
            titre = query.value(1)
            item = QListWidgetItem(titre)
            item.setData(Qt.ItemDataRole.UserRole, note_id)
            self.notes_list.addItem(item)

    def load_note(self, item):
        """Charge une note sélectionnée dans l'interface."""
        note_id = item.data(Qt.ItemDataRole.UserRole)
        query = QSqlQuery()
        query.prepare("SELECT titre, contenu, resume, rappel FROM notes WHERE id = ?")
        query.addBindValue(note_id)
        if query.exec() and query.next():
            self.title_input.setText(query.value(0))
            self.main_notes.setPlainText(query.value(1))
            self.summary.setPlainText(query.value(2))
            self.cue_column.setPlainText(query.value(3))

    def clear_fields(self):
        """Efface tous les champs pour une nouvelle note."""
        self.title_input.clear()
        self.main_notes.clear()
        self.cue_column.clear()
        self.summary.clear()
        self.notes_list.clearSelection()

    def delete_note(self):
        """Supprime la note sélectionnée."""
        if self.notes_list.currentItem():
            note_id = self.notes_list.currentItem().data(Qt.ItemDataRole.UserRole)
            reply = QMessageBox.question(self, "Confirmation",
                                         "Êtes-vous sûr de vouloir supprimer cette note ?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                query = QSqlQuery()
                query.prepare("DELETE FROM notes WHERE id = ?")
                query.addBindValue(note_id)
                if query.exec():
                    QMessageBox.information(self, "Succès", "Note supprimée avec succès")
                    self.load_notes_list()
                    self.clear_fields()
                else:
                    QMessageBox.critical(self, "Erreur", "Erreur lors de la suppression de la note")
        else:
            QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner une note à supprimer")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    if not DatabaseManager.init_db():
        print("Erreur lors de l'initialisation de la base de données")
        sys.exit(1)
    window = CornellNotesApp()
    window.show()
    sys.exit(app.exec())
