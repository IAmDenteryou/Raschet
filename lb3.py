import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
import random

MAX_PIN_ATTEMPTS = 3
CREDIT_PENALTY_RATE = 0.01


class Card:
    def __init__(self, card_number, pin, initial_balance=0.0, history_enabled=False, deposit_type='partial',
                 owner_name=""):
        self.card_number = card_number
        self.pin = pin
        self.balance = float(initial_balance)
        self.history_enabled = history_enabled
        self.transactions = []
        self.is_blocked = False
        self.deposit_type = deposit_type
        self.simulated_bank_account = random.uniform(1000, 10000)
        self.owner_name = owner_name

    def check_pin(self, entered_pin):
        return self.pin == entered_pin

    def get_balance_as_string(self):
        return f"{self.balance:.2f}"

    def add_transaction(self, trans_type, amount):
        timestamp = datetime.now()
        self.transactions.append((timestamp, trans_type, amount, self.balance))

        one_month_ago = timestamp - timedelta(days=30)
        current_transactions = []
        for t in self.transactions:
            if t[0] >= one_month_ago:
                current_transactions.append(t)
        self.transactions = current_transactions

    def get_history_as_string(self):
        if not self.history_enabled:
            return "История операций для данной карты недоступна."
        if not self.transactions:
            return "История операций пуста."

        history_report = "История операций (за последний месяц):\n"
        history_report += "Дата и время         | Тип          | Сумма    | Баланс после\n"
        history_report += "-" * 60 + "\n"
        for ts, trans_type, trans_amount, balance_after in reversed(self.transactions):
            amount_str = f"{trans_amount:.2f}" if trans_amount is not None else "N/A"
            history_report += f"{ts.strftime('%d.%m.%Y %H:%M')} | {trans_type:<12} | {amount_str:>8} | {balance_after:.2f}\n"
        return history_report

    def withdraw(self, amount, atm_cash_available):
        print("Ошибка: метод снятия не реализован для базового класса карты")
        return False, "Ошибка операции"

    def deposit_cash(self, amount):
        if amount <= 0:
            return False, "Сумма пополнения должна быть больше нуля."
        self.balance += amount
        self.add_transaction("Пополнение", amount)
        return True, f"Карта пополнена на {amount:.2f}. Новый баланс: {self.get_balance_as_string()}"

    def transfer_from_bank_account(self, amount_to_transfer=None):
        if self.deposit_type == 'full':
            if self.simulated_bank_account <= 0:
                return False, "На связанном банковском счете нет средств."
            transfer_amount = self.simulated_bank_account
            self.balance += transfer_amount
            self.simulated_bank_account = 0
            self.add_transaction("Перевод с БС", transfer_amount)
            return True, f"Вся сумма {transfer_amount:.2f} переведена с банк. счета. Баланс карты: {self.get_balance_as_string()}"

        elif self.deposit_type == 'partial':
            if amount_to_transfer is None or amount_to_transfer <= 0:
                return False, "Сумма перевода должна быть больше нуля."
            if amount_to_transfer > self.simulated_bank_account:
                return False, f"Недостаточно средств на банк. счете. Доступно: {self.simulated_bank_account:.2f}"
            self.balance += amount_to_transfer
            self.simulated_bank_account -= amount_to_transfer
            self.add_transaction("Перевод с БС", amount_to_transfer)
            return True, f"Сумма {amount_to_transfer:.2f} переведена с банк. счета. Баланс карты: {self.get_balance_as_string()}"

        return False, "Неизвестный вариант пополнения карты."


class DebitCard(Card):
    def withdraw(self, amount, atm_cash_available):
        if self.is_blocked:
            return False, "Карта заблокирована."
        if amount <= 0:
            return False, "Сумма снятия должна быть больше нуля."
        if amount > self.balance:
            return False, "Недостаточно средств на дебетовой карте."
        if amount > atm_cash_available:
            return False, "В банкомате недостаточно денег для этой операции."

        self.balance -= amount
        self.add_transaction("Снятие", amount)
        return True, f"Выдано: {amount:.2f}. Остаток на карте: {self.get_balance_as_string()}"


class CreditCard(Card):
    def __init__(self, card_number, pin, initial_balance=0.0, credit_limit=1000.0, history_enabled=False,
                 deposit_type='partial', owner_name=""):
        super().__init__(card_number, pin, initial_balance, history_enabled, deposit_type, owner_name)
        self.credit_limit = float(credit_limit)

    def _apply_penalty_if_negative(self):
        if self.balance < 0:
            penalty_amount = abs(self.balance * CREDIT_PENALTY_RATE)
            self.balance -= penalty_amount
            self.add_transaction("Пени", penalty_amount)

    def get_balance_as_string(self):
        self._apply_penalty_if_negative()
        return f"{self.balance:.2f} (Кредитный лимит: {self.credit_limit:.2f})"

    def withdraw(self, amount, atm_cash_available):
        if self.is_blocked:
            return False, "Карта заблокирована."
        self._apply_penalty_if_negative()

        if amount <= 0:
            return False, "Сумма снятия должна быть больше нуля."

        if (self.balance - amount) < -self.credit_limit:
            available_for_withdrawal = self.balance + self.credit_limit
            return False, f"Превышен кредитный лимит. Доступно для снятия с учетом кредита: {available_for_withdrawal:.2f}"

        if amount > atm_cash_available:
            return False, "В банкомате недостаточно денег для этой операции."

        self.balance -= amount
        self.add_transaction("Снятие", amount)
        self._apply_penalty_if_negative()
        return True, f"Выдано: {amount:.2f}. Остаток на карте: {self.get_balance_as_string()}"

    def deposit_cash(self, amount):
        self._apply_penalty_if_negative()
        success, message = super().deposit_cash(amount)
        if success:
            self._apply_penalty_if_negative()
            message = f"Карта пополнена на {amount:.2f}. Новый баланс: {self.get_balance_as_string()}"
        return success, message

    def transfer_from_bank_account(self, amount_to_transfer=None):
        self._apply_penalty_if_negative()
        success, message = super().transfer_from_bank_account(amount_to_transfer)
        if success:
            self._apply_penalty_if_negative()
            if self.deposit_type == 'full':
                message = f"Вся сумма переведена с банк. счета. Баланс карты: {self.get_balance_as_string()}"
            elif self.deposit_type == 'partial' and amount_to_transfer is not None:
                message = f"Сумма {amount_to_transfer:.2f} переведена с банк. счета. Баланс карты: {self.get_balance_as_string()}"
        return success, message


class ATM:
    def __init__(self, initial_atm_cash=50000.0):
        self.current_card = None
        self.pin_attempts = 0
        self.cash_in_atm = float(initial_atm_cash)
        self.session_transactions_for_receipt = []

    def insert_card(self, card_object):
        if card_object.is_blocked:
            return False, "Эта карта заблокирована."
        if random.random() < 0.03:
            return False, "Ошибка чтения карты. Попробуйте другую карту или вставьте эту еще раз."
        self.current_card = card_object
        self.pin_attempts = 0
        self.session_transactions_for_receipt = []
        return True, "Карта прочитана. Введите PIN-код."

    def process_pin_entry(self, pin):
        if not self.current_card:
            return "NO_CARD", "Сначала вставьте карту."

        if self.current_card.check_pin(pin):
            self.pin_attempts = 0
            return "SUCCESS", "PIN-код верный."
        else:
            self.pin_attempts += 1
            if self.pin_attempts >= MAX_PIN_ATTEMPTS:
                self.current_card.is_blocked = True
                self._confiscate_card("PIN-код неверно введен 3 раза.")
                return "BLOCKED", "Неверный PIN-код. Карта заблокирована и изъята."
            else:
                attempts_left = MAX_PIN_ATTEMPTS - self.pin_attempts
                return "FAILURE", f"Неверный PIN-код. Осталось попыток: {attempts_left}."

    def perform_withdrawal(self, amount_string):
        if not self.current_card: return "Нет карты."
        try:
            amount = float(amount_string)
            if amount <= 0: return "Сумма должна быть положительной."

            success, message = self.current_card.withdraw(amount, self.cash_in_atm)
            if success:
                self.cash_in_atm -= amount
                self.session_transactions_for_receipt.append(f"Снятие: {amount:.2f}")
            return message
        except ValueError:
            return "Неверный формат суммы."

    def perform_cash_deposit_to_card(self, amount_string):
        if not self.current_card: return "Нет карты."
        try:
            amount = float(amount_string)
            success, message = self.current_card.deposit_cash(amount)
            if success:
                self.cash_in_atm += amount
                self.session_transactions_for_receipt.append(f"Внесение наличных: {amount:.2f}")
            return message
        except ValueError:
            return "Неверный формат суммы."

    def perform_transfer_from_bank_to_card(self, amount_string=None):
        if not self.current_card: return "Нет карты."

        card = self.current_card
        if card.deposit_type == 'full':
            success, message = card.transfer_from_bank_account()
            if success: self.session_transactions_for_receipt.append("Перевод с банк. счета (вся сумма)")
            return message
        elif card.deposit_type == 'partial':
            if amount_string is None: return "Нужно указать сумму для частичного перевода."
            try:
                amount = float(amount_string)
                success, message = card.transfer_from_bank_account(amount)
                if success: self.session_transactions_for_receipt.append(f"Перевод с банк. счета: {amount:.2f}")
                return message
            except ValueError:
                return "Неверный формат суммы."
        return "Неизвестный тип карты для этой операции."

    def request_card_balance(self):
        if not self.current_card: return "Нет карты."
        balance_info = self.current_card.get_balance_as_string()
        self.session_transactions_for_receipt.append("Запрос баланса")
        return f"Текущий баланс: {balance_info}"

    def request_card_history(self):
        if not self.current_card: return "Нет карты."
        if not self.current_card.history_enabled:
            return "История операций для этой карты недоступна."

        self.session_transactions_for_receipt.append("Запрос истории операций")
        return self.current_card.get_history_as_string()

    def print_receipt(self, receipt_text):
        full_receipt_text = "--- ЧЕК ---\n"
        full_receipt_text += f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        if self.current_card:
            full_receipt_text += f"Карта: **** **** **** {self.current_card.card_number[-4:]}\n"
        full_receipt_text += "----------------\n"
        full_receipt_text += receipt_text + "\n----------------\nСпасибо!\n"

        print("\n--- ПЕЧАТЬ ЧЕКА ---")  # Для отладки, можно убрать
        print(full_receipt_text)
        messagebox.showinfo("Чек", full_receipt_text)

    def cancel_operation_and_eject_card(self):
        operation_report = "Операция отменена.\n"
        if self.session_transactions_for_receipt:
            operation_report += "Выполненные операции:\n"
            for op in self.session_transactions_for_receipt:
                operation_report += f"- {op}\n"
        else:
            operation_report += "Операций не было.\n"

        self.print_receipt(operation_report)
        return self._eject_card_to_user()

    def _eject_card_to_user(self):
        card_to_return = self.current_card
        self.current_card = None
        self.pin_attempts = 0
        self.session_transactions_for_receipt = []
        if card_to_return:
            return f"Карта {card_to_return.card_number} возвращена."
        return "Нет карты для возврата."

    def _confiscate_card(self, reason=""):
        if self.current_card:
            print(f"СИСТЕМНОЕ СООБЩЕНИЕ: Карта {self.current_card.card_number} изъята. Причина: {reason}")
        self.current_card = None
        self.pin_attempts = 0
        self.session_transactions_for_receipt = []


class ATMGUI(tk.Tk):
    def __init__(self, atm_logic, card_database):
        super().__init__()
        self.atm = atm_logic
        self.cards = card_database
        self.title("Банкомат")
        self.geometry("550x480")  # Немного увеличил высоту для русского текста
        self.resizable(False, False)

        self.active_frame = None
        self.pin_buffer = ""

        self._show_welcome_screen()

    def _clear_screen(self):
        if self.active_frame:
            self.active_frame.destroy()
        self.active_frame = tk.Frame(self, padx=15, pady=15)
        self.active_frame.pack(expand=True, fill=tk.BOTH)

    def _show_welcome_screen(self):
        self._clear_screen()
        self.title("Банкомат - Ожидание карты")

        tk.Label(self.active_frame, text="Добро пожаловать!", font=("Arial", 20)).pack(pady=15)
        tk.Label(self.active_frame, text="Вставьте карту (выберите из списка ниже):", font=("Arial", 12)).pack(pady=10)

        self.selected_card_var = tk.StringVar(self)
        if self.cards:
            card_list_for_menu = [f"{number} ({c.owner_name}, {'Забл.' if c.is_blocked else 'OK'})" for number, c in
                                  self.cards.items()]
            if card_list_for_menu:
                self.selected_card_var.set(card_list_for_menu[0])
            card_option_menu = tk.OptionMenu(self.active_frame, self.selected_card_var,
                                             *card_list_for_menu if card_list_for_menu else ["Нет карт"])
            card_option_menu.pack(pady=5)
            tk.Button(self.active_frame, text="Вставить карту", command=self._handle_card_insertion,
                      font=("Arial", 12)).pack(pady=15)
        else:
            tk.Label(self.active_frame, text="В базе нет карт для симуляции.", font=("Arial", 10), fg="red").pack()

        tk.Label(self.active_frame, text=f"В банкомате: {self.atm.cash_in_atm:.2f} руб.", font=("Arial", 9)).pack(
            side=tk.BOTTOM, pady=3)

    def _handle_card_insertion(self):
        selected_card_string = self.selected_card_var.get()
        if not selected_card_string or "Нет карт" in selected_card_string:
            messagebox.showwarning("Ошибка", "Карта не выбрана.")
            return

        card_number_from_string = selected_card_string.split(" ")[0]

        if card_number_from_string in self.cards:
            card_object = self.cards[card_number_from_string]
            success, message = self.atm.insert_card(card_object)
            if success:
                self._show_pin_entry_screen(message)
            else:
                messagebox.showerror("Ошибка карты", message)
                self._show_welcome_screen()
        else:
            messagebox.showerror("Ошибка", "Карта не найдена в системе.")

    def _show_pin_entry_screen(self, initial_message=""):
        self._clear_screen()
        self.title("Банкомат - Ввод PIN")
        self.pin_buffer = ""

        tk.Label(self.active_frame, text=initial_message, font=("Arial", 12)).pack(pady=10)

        self.pin_display_var = tk.StringVar()
        tk.Label(self.active_frame, textvariable=self.pin_display_var, font=("Arial", 18, "bold"), width=8,
                 relief=tk.GROOVE).pack(pady=10)

        keypad_frame = tk.Frame(self.active_frame)
        keypad_frame.pack(pady=5)

        pinpad_buttons = [
            '1', '2', '3',
            '4', '5', '6',
            '7', '8', '9',
            'Отмена', '0', 'Стереть'
        ]
        row, col = 0, 0
        for button_text in pinpad_buttons:
            button_command = None
            button_color = "lightgrey"
            if button_text.isdigit():
                button_command = lambda digit=button_text: self._add_digit_to_pin(digit)
            elif button_text == "Стереть":
                button_command = self._clear_pin_entry
                button_color = "orange"
            elif button_text == "Отмена":
                button_command = self._cancel_button_pressed_on_pin_screen
                button_color = "salmon"

            tk.Button(keypad_frame, text=button_text, width=5, height=2, font=("Arial", 10), bg=button_color,
                      command=button_command).grid(row=row, column=col, padx=3, pady=3)
            col += 1
            if col > 2:
                col = 0
                row += 1

        tk.Button(self.active_frame, text="Ввод (OK)", command=self._submit_pin_entry, font=("Arial", 12),
                  bg="lightgreen").pack(pady=10)

    def _add_digit_to_pin(self, digit):
        if len(self.pin_buffer) < 4:
            self.pin_buffer += digit
            self.pin_display_var.set("*" * len(self.pin_buffer))

    def _clear_pin_entry(self):
        self.pin_buffer = ""
        self.pin_display_var.set("")

    def _cancel_button_pressed_on_pin_screen(self):
        return_message = self.atm.cancel_operation_and_eject_card()
        messagebox.showinfo("Отмена", return_message)
        self._show_welcome_screen()

    def _submit_pin_entry(self):
        status, message = self.atm.process_pin_entry(self.pin_buffer)
        if status == "SUCCESS":
            messagebox.showinfo("PIN-код", message)
            self._show_main_menu()
        elif status == "FAILURE":
            messagebox.showwarning("PIN-код", message)
            self._clear_pin_entry()
        elif status == "BLOCKED":
            messagebox.showerror("PIN-код", message)
            self._show_welcome_screen()
        elif status == "NO_CARD":
            messagebox.showerror("Ошибка", message)
            self._show_welcome_screen()

    def _show_main_menu(self):
        self._clear_screen()
        card_num_suffix = self.atm.current_card.card_number[-4:] if self.atm.current_card else "????"
        self.title(f"Банкомат - Главное Меню (Карта *{card_num_suffix})")

        tk.Label(self.active_frame, text="Выберите операцию:", font=("Arial", 16)).pack(pady=15)

        operations = [
            ("Снять наличные", self._show_withdrawal_screen),
            ("Внести наличные на карту", self._show_deposit_screen),
            ("Перевести с банк. счета на карту", self._show_transfer_from_bank_screen),
            ("Узнать баланс", self._show_balance_screen),
        ]
        if self.atm.current_card and self.atm.current_card.history_enabled:
            operations.append(("Посмотреть историю", self._show_history_screen))

        for name, command in operations:
            tk.Button(self.active_frame, text=name, command=command, font=("Arial", 12), width=30, height=1).pack(
                pady=4)

        tk.Button(self.active_frame, text="Завершить и вернуть карту", command=self._cancel_button_pressed_in_main_menu,
                  font=("Arial", 12), bg="orange", width=30).pack(pady=20)

    def _cancel_button_pressed_in_main_menu(self):
        return_message = self.atm.cancel_operation_and_eject_card()
        messagebox.showinfo("Завершение работы", return_message)
        self._show_welcome_screen()

    def _create_amount_entry_screen(self, window_title, prompt_text, amount_processing_function):
        self._clear_screen()
        self.title(f"Банкомат - {window_title}")
        tk.Label(self.active_frame, text=prompt_text, font=("Arial", 14)).pack(pady=15)

        entry_field = tk.Entry(self.active_frame, font=("Arial", 14), width=12, justify=tk.RIGHT)
        entry_field.pack(pady=10)
        entry_field.focus()

        def on_ok_pressed():
            entered_amount_string = entry_field.get()
            if not entered_amount_string:
                messagebox.showwarning("Внимание", "Введите сумму.")
                return
            try:
                float(entered_amount_string)
                if float(entered_amount_string) <= 0:
                    messagebox.showwarning("Внимание", "Сумма должна быть положительной.")
                    return
            except ValueError:
                messagebox.showwarning("Внимание", "Некорректная сумма.")
                return

            result_message = amount_processing_function(entered_amount_string)
            messagebox.showinfo(window_title, result_message)
            if ("Выдано" in result_message or "пополнена" in result_message or "переведена" in result_message) and \
                    "Недостаточно" not in result_message and "Превышен" not in result_message and "Ошибка" not in result_message:
                receipt_content = f"Операция: {window_title}\nСумма: {entered_amount_string}\nСтатус: Успешно\n{self.atm.request_card_balance()}"
                self.atm._print_receipt(receipt_content)
            self._show_main_menu()

        tk.Button(self.active_frame, text="OK", command=on_ok_pressed, font=("Arial", 12), width=8).pack(side=tk.LEFT,
                                                                                                         padx=10,
                                                                                                         pady=10)
        tk.Button(self.active_frame, text="Отмена (в меню)", command=self._show_main_menu, font=("Arial", 12),
                  width=15).pack(side=tk.RIGHT, padx=10, pady=10)
        tk.Button(self.active_frame, text="Отменить и вернуть карту", command=self._cancel_button_pressed_in_main_menu,
                  font=("Arial", 9)).pack(side=tk.BOTTOM, pady=5)

    def _show_withdrawal_screen(self):
        self._create_amount_entry_screen(
            "Снятие наличных",
            "Введите сумму для снятия:",
            self.atm.perform_withdrawal
        )

    def _show_deposit_screen(self):
        self._create_amount_entry_screen(
            "Внесение наличных",
            "Введите сумму для внесения на карту:",
            self.atm.perform_cash_deposit_to_card
        )

    def _show_transfer_from_bank_screen(self):
        card = self.atm.current_card
        if not card:
            messagebox.showerror("Ошибка", "Нет вставленной карты.")
            self._show_welcome_screen()
            return

        if card.deposit_type == 'full':
            self._clear_screen()
            self.title("Банкомат - Перевод всей суммы с банк. счета")
            available_on_account = card.simulated_bank_account
            tk.Label(self.active_frame,
                     text=f"Эта карта позволяет перевести только всю сумму.\nНа вашем виртуальном банк. счете: {available_on_account:.2f} руб.\nПеревести?",
                     font=("Arial", 12)).pack(pady=15)

            def confirm_full_transfer():
                result_message = self.atm.perform_transfer_from_bank_to_card()
                messagebox.showinfo("Перевод с банк. счета", result_message)
                if "переведена" in result_message and "Ошибка" not in result_message:
                    receipt_content = f"Операция: Перевод с банк. счета (вся сумма)\nСтатус: Успешно\n{self.atm.request_card_balance()}"
                    self.atm._print_receipt(receipt_content)
                self._show_main_menu()

            tk.Button(self.active_frame, text="Да, перевести", command=confirm_full_transfer, font=("Arial", 12),
                      bg="lightgreen").pack(pady=10)
            tk.Button(self.active_frame, text="Нет, вернуться в меню", command=self._show_main_menu,
                      font=("Arial", 12)).pack(pady=5)
            tk.Button(self.active_frame, text="Отменить и вернуть карту",
                      command=self._cancel_button_pressed_in_main_menu, font=("Arial", 9)).pack(side=tk.BOTTOM, pady=5)

        elif card.deposit_type == 'partial':
            available_on_account = card.simulated_bank_account
            self._create_amount_entry_screen(
                "Перевод с банк. счета на карту",
                f"Введите сумму для перевода (доступно на банк. счете: {available_on_account:.2f}):",
                self.atm.perform_transfer_from_bank_to_card
            )
        else:
            messagebox.showerror("Ошибка", "Неизвестный тип пополнения для карты.")
            self._show_main_menu()

    def _show_balance_screen(self):
        self._clear_screen()
        self.title("Банкомат - Баланс карты")
        balance_information = self.atm.request_card_balance()
        tk.Label(self.active_frame, text=balance_information, font=("Arial", 14)).pack(pady=25)

        tk.Button(self.active_frame, text="Напечатать баланс (чек)",
                  command=lambda: self.atm._print_receipt(balance_information),
                  font=("Arial", 12)).pack(pady=10)
        tk.Button(self.active_frame, text="Вернуться в меню", command=self._show_main_menu, font=("Arial", 12)).pack(
            pady=5)
        tk.Button(self.active_frame, text="Отменить и вернуть карту", command=self._cancel_button_pressed_in_main_menu,
                  font=("Arial", 9)).pack(side=tk.BOTTOM, pady=5)

    def _show_history_screen(self):
        self._clear_screen()
        self.title("Банкомат - История операций")

        history_text_content = self.atm.request_card_history()

        text_area_widget = tk.Text(self.active_frame, wrap=tk.WORD, font=("Courier New", 9), height=12, width=65)
        text_area_widget.insert(tk.END, history_text_content)
        text_area_widget.config(state=tk.DISABLED)

        scrollbar_widget = tk.Scrollbar(self.active_frame, command=text_area_widget.yview)
        text_area_widget.config(yscrollcommand=scrollbar_widget.set)

        scrollbar_widget.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        text_area_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=10, padx=(10, 0))

        buttons_frame = tk.Frame(self.active_frame)
        buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 10))

        tk.Button(buttons_frame, text="Напечатать историю (чек)",
                  command=lambda: self.atm._print_receipt(history_text_content),
                  font=("Arial", 10)).pack(pady=3)
        tk.Button(buttons_frame, text="Вернуться в меню", command=self._show_main_menu, font=("Arial", 10)).pack(pady=3)
        tk.Button(buttons_frame, text="Отменить и вернуть карту", command=self._cancel_button_pressed_in_main_menu,
                  font=("Arial", 9)).pack(pady=3)


if __name__ == "__main__":
    available_cards_data = {
        "1111-2222-3333-4444": DebitCard("1111-2222-3333-4444", "1234", 1500.00, True, 'partial', "Иванов И.И."),
        "5555-6666-7777-8888": CreditCard("5555-6666-7777-8888", "5678", 500.00, 2000.00, True, 'partial',
                                          "Петрова А.А."),
        "9999-0000-1111-2222": DebitCard("9999-0000-1111-2222", "0000", 100.00, False, 'full', "Сидоров С.С."),
        "1234-5678-9012-3456": CreditCard("1234-5678-9012-3456", "1111", -150.00, 500.00, True, 'full', "Зайцев В.В."),
    }

    card_with_history = available_cards_data["1111-2222-3333-4444"]
    # Очищаем и заполняем историю корректно
    card_with_history.transactions = []  # Очищаем старые транзакции для чистоты теста
    card_with_history.balance = 1200.0
    card_with_history.add_transaction("Начальный баланс", None)

    salary_amount = 2000.0
    card_with_history.balance += salary_amount  # Сначала меняем баланс
    card_with_history.add_transaction("Зарплата", salary_amount)  # Потом добавляем транзакцию

    purchase_amount = 300.0
    card_with_history.balance -= purchase_amount
    card_with_history.add_transaction("Покупка", purchase_amount)

    withdrawal_amount = 500.0
    card_with_history.balance -= withdrawal_amount
    card_with_history.add_transaction("Снятие", withdrawal_amount)

    old_date = datetime.now() - timedelta(days=35)
    card_with_history.transactions.insert(0, (old_date, "Старое пополнение", 10.0, 10.0))

    atm_logic_instance = ATM(initial_atm_cash=25000.00)

    app_gui = ATMGUI(atm_logic_instance, available_cards_data)
    app_gui.mainloop()