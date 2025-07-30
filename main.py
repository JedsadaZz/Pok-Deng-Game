# Pok-Deng game built with FastAPI and Python.

# main.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import random

app = FastAPI()

# --- Game Logic ---

class Card(BaseModel):
    """Represents a single playing card."""
    suit: str
    rank: str
    value: int

class Player(BaseModel):
    """Represents a player with a hand of cards, a score, and chips."""
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
    """Calculates the score of a hand in Pok Deng (the last digit of the sum)."""
    return sum(card.value for card in hand) % 10

# --- Game State ---
# These are global variables that hold the state of the game.
player = Player()
dealer = Player()
deck = create_deck()

# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serves the main HTML frontend for the game."""
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Pok Deng</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-100 flex items-center justify-center h-screen font-sans">
            <div class="bg-white p-8 rounded-lg shadow-2xl w-full max-w-md">
                <h1 class="text-3xl font-bold mb-4 text-center text-gray-800">Pok Deng</h1>
                <div id="game-state" class="text-center mb-6">
                    <p class="text-lg text-gray-600">Your Chips: <span id="player-chips" class="font-bold text-indigo-600">100</span></p>
                </div>

                <!-- Controls for placing a bet and playing a round -->
                <div id="play-controls">
                    <div class="mb-4">
                        <label for="bet" class="block text-sm font-medium text-gray-700">Place Your Bet:</label>
                        <input type="number" id="bet" name="bet" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500" value="5" min="1">
                    </div>
                    <button id="play-button" onclick="playRound()" class="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-300">
                        Play
                    </button>
                </div>

                <!-- "New Game" button, hidden by default -->
                <button id="new-game-button" onclick="startNewGame()" class="hidden w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 mt-4 transition-colors duration-300">
                    New Game
                </button>

                <!-- Area to display game results -->
                <div id="result" class="mt-6 text-center"></div>
            </div>

            <script>
                // Handles the logic for playing a single round
                async function playRound() {
                    const betAmount = document.getElementById('bet').value;
                    const playerChips = parseInt(document.getElementById('player-chips').innerText);

                    // Basic client-side validation
                    if (betAmount <= 0) {
                        document.getElementById('result').innerHTML = `<p class="text-red-500 font-bold">Please enter a bet greater than zero.</p>`;
                        return;
                    }
                    if (parseInt(betAmount) > playerChips) {
                        document.getElementById('result').innerHTML = `<p class="text-red-500 font-bold">You don't have enough chips for that bet.</p>`;
                        return;
                    }

                    const response = await fetch(`/play?bet=${betAmount}`);
                    const data = await response.json();

                    const resultDiv = document.getElementById('result');
                    const playerChipsSpan = document.getElementById('player-chips');

                    // Handle errors from the server
                    if (data.error) {
                        resultDiv.innerHTML = `<p class="text-red-500 font-bold">${data.error}</p>`;
                        return;
                    }

                    // Display hands, scores, and the round result
                    resultDiv.innerHTML = `
                        <p class="text-lg font-semibold text-gray-800">Your Hand: ${data.player_hand.map(c => `${c.rank} of ${c.suit}`).join(', ')} (Score: ${data.player_score})</p>
                        <p class="text-lg font-semibold text-gray-800">Dealer's Hand: ${data.dealer_hand.map(c => `${c.rank} of ${c.suit}`).join(', ')} (Score: ${data.dealer_score})</p>
                        <p class="text-2xl font-bold mt-4 ${data.result === 'You win!' ? 'text-green-500' : data.result === 'You lose!' ? 'text-red-500' : 'text-gray-500'}">${data.result}</p>
                    `;
                    playerChipsSpan.innerText = data.player_chips;

                    // Check for Game Over condition
                    if (data.game_over) {
                        resultDiv.innerHTML += `<p class="text-4xl font-bold text-red-700 mt-4">GAME OVER</p>`;
                        document.getElementById('play-controls').classList.add('hidden');
                        document.getElementById('new-game-button').classList.remove('hidden');
                    }
                }

                // Handles the logic for starting a new game
                async function startNewGame() {
                    const response = await fetch('/new_game', { method: 'POST' });
                    const data = await response.json();

                    // Reset the UI to the initial state
                    document.getElementById('player-chips').innerText = data.player_chips;
                    document.getElementById('result').innerHTML = '';
                    document.getElementById('play-controls').classList.remove('hidden');
                    document.getElementById('new-game-button').classList.add('hidden');
                    document.getElementById('bet').value = 5;
                }
            </script>
        </body>
    </html>
    """

@app.get("/play")
async def play_round(bet: int):
    """Handles a single round of the game, dealing cards and determining the winner."""
    global deck, player, dealer

    # Server-side validation for the bet
    if bet <= 0:
        return {"error": "Bet must be a positive number."}
    if player.chips < bet:
        return {"error": "Not enough chips to place that bet."}

    # Reshuffle the deck if it's running low on cards
    if len(deck) < 4:
        deck = create_deck()
    random.shuffle(deck)

    # Deal cards to player and dealer
    player.hand = [deck.pop(), deck.pop()]
    dealer.hand = [deck.pop(), deck.pop()]

    player.score = calculate_score(player.hand)
    dealer.score = calculate_score(dealer.hand)

    # Determine the result and update player's chips
    result = ""
    if player.score > dealer.score:
        result = "You win!"
        player.chips += bet
    elif player.score < dealer.score:
        result = "You lose!"
        player.chips -= bet
    else:
        result = "It's a tie!"

    # Check for the "Game Over" condition
    game_over = player.chips <= 0

    return {
        "player_hand": player.hand,
        "dealer_hand": dealer.hand,
        "player_score": player.score,
        "dealer_score": dealer.score,
        "result": result,
        "player_chips": player.chips,
        "game_over": game_over
    }

@app.post("/new_game")
async def new_game():
    """Resets the game state, allowing the player to start over."""
    global player, dealer, deck
    # Re-initialize the global state variables
    player = Player()
    dealer = Player()
    deck = create_deck()
    return {"message": "New game started.", "player_chips": player.chips}