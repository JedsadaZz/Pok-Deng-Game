# Pok-Deng game built with FastAPI and Python.

# main.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import random

app = FastAPI()

# --- Game Logic ---

class Card(BaseModel):
    suit: str
    rank: str
    value: int

class Player(BaseModel):
    hand: list[Card] = []
    score: int = 0
    chips: int = 100

def create_deck():
    """Creates a standard 52-card deck."""
    suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    ranks = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
        "10": 0, "Jack": 0, "Queen": 0, "King": 0, "Ace": 1
    }
    return [Card(suit=s, rank=r, value=v) for s in suits for r, v in ranks.items()]

def calculate_score(hand: list[Card]):
    """Calculates the score of a hand in Pok Deng."""
    return sum(card.value for card in hand) % 10

# --- API Endpoints ---

player = Player()
dealer = Player()
deck = create_deck()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serves the HTML frontend."""
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Pok Deng</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-100 flex items-center justify-center h-screen">
            <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
                <h1 class="text-3xl font-bold mb-4 text-center">Pok Deng</h1>
                <div id="game-state" class="text-center mb-4">
                    <p class="text-lg">Your Chips: <span id="player-chips">100</span></p>
                </div>
                <div class="mb-4">
                    <label for="bet" class="block text-sm font-medium text-gray-700">Place Your Bet:</label>
                    <input type="number" id="bet" name="bet" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" value="5">
                </div>
                <button onclick="playRound()" class="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                    Play
                </button>
                <div id="result" class="mt-6 text-center"></div>
            </div>

            <script>
                async function playRound() {
                    const betAmount = document.getElementById('bet').value;
                    const response = await fetch(`/play?bet=${betAmount}`);
                    const data = await response.json();

                    const resultDiv = document.getElementById('result');
                    resultDiv.innerHTML = `
                        <p class="text-lg font-semibold">Your Hand: ${data.player_hand.map(c => `${c.rank} of ${c.suit}`).join(', ')} (Score: ${data.player_score})</p>
                        <p class="text-lg font-semibold">Dealer's Hand: ${data.dealer_hand.map(c => `${c.rank} of ${c.suit}`).join(', ')} (Score: ${data.dealer_score})</p>
                        <p class="text-2xl font-bold mt-4 ${data.result === 'You win!' ? 'text-green-500' : data.result === 'You lose!' ? 'text-red-500' : 'text-gray-500'}">${data.result}</p>
                    `;

                    document.getElementById('player-chips').innerText = data.player_chips;
                }
            </script>
        </body>
    </html>
    """

@app.get("/play")
async def play_round(bet: int):
    """Handles a round of the game."""
    global deck, player, dealer

    # Reset hands and shuffle deck if it's low
    if len(deck) < 4:
        deck = create_deck()

    random.shuffle(deck)

    player.hand = [deck.pop(), deck.pop()]
    dealer.hand = [deck.pop(), deck.pop()]

    player.score = calculate_score(player.hand)
    dealer.score = calculate_score(dealer.hand)

    result = ""
    if player.score > dealer.score:
        result = "You win!"
        player.chips += bet
    elif player.score < dealer.score:
        result = "You lose!"
        player.chips -= bet
    else:
        result = "It's a tie!"

    return {
        "player_hand": player.hand,
        "dealer_hand": dealer.hand,
        "player_score": player.score,
        "dealer_score": dealer.score,
        "result": result,
        "player_chips": player.chips
    }
