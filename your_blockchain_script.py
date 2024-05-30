import hashlib
import json
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        # Создание начального блока
        self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Создание нового блока в блокчейне
        
        :param proof: Доказательство выполненной работы
        :param previous_hash: Хеш предыдущего блока
        :return: Новый блок
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Сброс текущего списка транзакций
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Создание новой транзакции для добавления в следующий блок

        :param sender: Адрес отправителя
        :param recipient: Адрес получателя
        :param amount: Сумма
        :return: Индекс блока, который будет содержать эту транзакцию
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        Создание SHA-256 хеша блока

        :param block: Блок
        :return: Хеш блока
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        # Возвращает последний блок в цепочке
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        Простой алгоритм доказательства работы:
        - Найдите число p' такое, что hash(pp') содержит 4 ведущих нуля, где p - предыдущий p'
        - p - предыдущее доказательство, а p' - новое доказательство

        :param last_proof: Предыдущее доказательство
        :return: Новое доказательство
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Подтверждает доказательство: содержит ли hash(last_proof, proof) 4 ведущих нуля?

        :param last_proof: Предыдущее доказательство
        :param proof: Текущее доказательство
        :return: True если доказательство верно, False если нет
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

# Создание экземпляра узла
app = Flask(__name__)

# Создание уникального адреса для этого узла
node_identifier = str(uuid4()).replace('-', '')

# Создание экземпляра блокчейна
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    # Мы запускаем алгоритм доказательства работы, чтобы получить следующее доказательство...
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Мы должны получить вознаграждение за найденное доказательство
    # Отправитель "0" означает, что узел заработал монету
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Создание нового блока, добавление его в цепочку
    block = blockchain.new_block(proof)

    response = {
        'message': "Новый блок сгенерирован",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Проверка необходимых полей
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Создание новой транзакции
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

# Запуск сервера
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
