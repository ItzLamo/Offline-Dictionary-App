import tkinter as tk
from tkinter import ttk, messagebox
import speech_recognition as sr
import pyttsx3
from googletrans import Translator
from typing import Optional, Dict, Any
import json
import os
from datetime import datetime
from nltk.corpus import wordnet
import nltk

# Download Those required data
nltk.download('wordnet')
nltk.download('omw-1.4')

class WordNetDictionary:
    def get_word_data(self, word: str) -> Dict[str, Any]:
        """Get word data from WordNet"""
        synsets = wordnet.synsets(word)
        
        if not synsets:
            raise ValueError(f"Word '{word}' not found")
            
        result = {
            "word": word,
            "definitions": [],
            "examples": [],
            "synonyms": set(),
            "antonyms": set()
        }
        
        for synset in synsets:
            # Add definition
            result["definitions"].append(synset.definition())
            
            # Add examples
            result["examples"].extend(synset.examples())
            
            # Add synonyms and antonyms
            for lemma in synset.lemmas():
                if lemma.name() != word:
                    result["synonyms"].add(lemma.name())
                if lemma.antonyms():
                    result["antonyms"].add(lemma.antonyms()[0].name())
        
        result["synonyms"] = list(result["synonyms"])
        result["antonyms"] = list(result["antonyms"])
        
        return result

class VoiceManager:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        
    def listen(self) -> str:
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source, timeout=5)
            return self.recognizer.recognize_google(audio)
            
    def speak(self, text: str):
        self.engine.say(text)
        self.engine.runAndWait()

class HistoryManager:
    def __init__(self):
        self.history_file = "dictionary_history.json"
        self.history = self.load_history()

    def load_history(self) -> list:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def add_entry(self, word: str, definition: str):
        self.history.append({
            'word': word,
            'definition': definition,
            'timestamp': datetime.now().isoformat()
        })
        self.save_history()

    def save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.history[-50:], f)  # Keep last 50 searches

class DictionaryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Offline Dictionary")
        self.root.geometry("1400x500")
        
        # Initialize components
        self.dictionary = WordNetDictionary()
        self.voice_manager = VoiceManager()
        self.translator = Translator()
        self.history_manager = HistoryManager()
        
        # Theme configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.create_widgets()
        self.setup_bindings()

    def create_widgets(self):
        # Main container with padding
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        self.create_search_section()
        
        self.create_results_section()
        
        self.create_translation_section()
        
        self.create_history_section()

    def create_search_section(self):
        search_frame = ttk.LabelFrame(self.main_frame, text="Search", padding="10")
        search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Word input
        self.word_entry = ttk.Entry(search_frame, width=40)
        self.word_entry.grid(row=0, column=0, padx=5)
        
        # Voice button
        voice_btn = ttk.Button(search_frame, text="🎤", command=self.voice_input, width=3)
        voice_btn.grid(row=0, column=1, padx=5)
        
        # Search button
        search_btn = ttk.Button(search_frame, text="Search", command=self.search_word)
        search_btn.grid(row=0, column=2, padx=5)

    def create_results_section(self):
        results_frame = ttk.LabelFrame(self.main_frame, text="Definition", padding="10")
        results_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=(0, 10))
        
        # Results text
        self.result_text = tk.Text(results_frame, wrap=tk.WORD, height=10)
        self.result_text.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.result_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.result_text.configure(yscrollcommand=scrollbar.set)

    def create_translation_section(self):
        translation_frame = ttk.LabelFrame(self.main_frame, text="Translation", padding="10")
        translation_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=(0, 10))
        
        # Language selection with codes
        self.languages = {
            "Spanish (es)": "es",
            "French (fr)": "fr",
            "German (de)": "de",
            "Chinese (zh)": "zh-cn",
            "Japanese (ja)": "ja"
        }
        
        self.translate_lang = ttk.Combobox(
            translation_frame, 
            values=list(self.languages.keys()),
            state="readonly"
        )
        self.translate_lang.set("Spanish (es)")
        self.translate_lang.grid(row=0, column=0, padx=5, pady=5)
        
        # Translation result
        self.translation_text = tk.Text(translation_frame, wrap=tk.WORD, height=8)
        self.translation_text.grid(row=1, column=0, sticky="nsew", pady=5)

    def create_history_section(self):
        history_frame = ttk.LabelFrame(self.main_frame, text="Search History", padding="10")
        history_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        
        self.history_text = tk.Text(history_frame, wrap=tk.WORD, height=6)
        self.history_text.grid(row=0, column=0, sticky="nsew")
        
        history_scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_text.yview)
        history_scrollbar.grid(row=0, column=1, sticky="ns")
        self.history_text.configure(yscrollcommand=history_scrollbar.set)

    def setup_bindings(self):
        self.word_entry.bind('<Return>', lambda e: self.search_word())
        self.translate_lang.bind('<<ComboboxSelected>>', lambda e: self.translate_word())

    def voice_input(self):
        try:
            text = self.voice_manager.listen()
            self.word_entry.delete(0, tk.END)
            self.word_entry.insert(0, text)
            self.search_word()
        except sr.UnknownValueError:
            messagebox.showerror("Error", "Could not understand audio")
        except sr.RequestError:
            messagebox.showerror("Error", "Could not request results from speech recognition service")
        except Exception as e:
            messagebox.showerror("Error", f"Voice input error: {str(e)}")

    def search_word(self):
        word = self.word_entry.get().strip()
        if not word:
            messagebox.showwarning("Warning", "Please enter a word")
            return
            
        try:
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            
            data = self.dictionary.get_word_data(word)
            
            # Format and display results
            result = f"Word: {word.capitalize()}\n\n"
            
            result += "Definitions:\n"
            for i, definition in enumerate(data["definitions"], 1):
                result += f"{i}. {definition}\n"
            
            if data["examples"]:
                result += "\nExamples:\n"
                for i, example in enumerate(data["examples"], 1):
                    result += f"{i}. {example}\n"
            
            if data["synonyms"]:
                result += "\nSynonyms:\n"
                result += ", ".join(data["synonyms"])
            
            if data["antonyms"]:
                result += "\nAntonyms:\n"
                result += ", ".join(data["antonyms"])
            
            self.result_text.insert(tk.END, result)
            self.result_text.config(state=tk.DISABLED)
            
            # Add to history
            self.history_manager.add_entry(word, data["definitions"][0] if data["definitions"] else "No definition available")
            self.update_history_display()
            
            # Auto-translate
            self.translate_word()
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Search error: {str(e)}")

    def translate_word(self):
        word = self.word_entry.get().strip()
        if not word:
            return
            
        try:
            self.translation_text.config(state=tk.NORMAL)
            self.translation_text.delete(1.0, tk.END)
            
            selected_language = self.translate_lang.get()
            target_lang = self.languages[selected_language]
            
            translation = self.translator.translate(
                word,
                dest=target_lang
            )
            
            result = f"Translation: {translation.text}\n"
            result += f"Pronunciation: {translation.pronunciation if translation.pronunciation else translation.text}"
            
            self.translation_text.insert(tk.END, result)
            self.translation_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.translation_text.insert(tk.END, f"Translation error: {str(e)}")
            self.translation_text.config(state=tk.DISABLED)

    def update_history_display(self):
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)
        
        for entry in reversed(self.history_manager.history):
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%Y-%m-%d %H:%M")
            self.history_text.insert(tk.END, f"{timestamp} - {entry['word']}: {entry['definition'][:100]}...\n")
        
        self.history_text.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = DictionaryApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()