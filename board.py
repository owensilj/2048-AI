import logging
import random

import numpy as np
from graphics import *
from pynput import keyboard

# Logging configuration
config = "%(asctime)s [%(levelname)s]:%(name)s - %(message)s"
logging.basicConfig(format=config, filename='board_log.log', level=logging.DEBUG, filemode="w")
board_log = logging.getLogger("main")
board_log.setLevel(logging.INFO)

# Can disable logging for perf improvements here
board_log.disabled = True


class Board:
	def __init__(self, size=4, graphics=1):
		"""
		Initialzier for 2048 game board
		Args:
			size: Integer size of the board, must be greater than 0. Size represents the square size
				(e.g. 8 would be a chessboard). Default size is 4.
			graphics: Integer to enable graphics. 0 to disable, 1 to enable (default 1)
		"""
		board_log.log(logging.INFO, str("Initialize board with size " + str(size) + " and graphics: " + str(graphics)))
		random.seed(None)
		self._board = np.zeros(size ** 2, int)
		self._size = size
		self._win_size = None
		self._win = None
		self.game_ended = False
		self._spawn_piece()
		self._key_listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
		if graphics == 1:
			self._win_size = 900
			self._win = GraphWin("2048 AI", self._win_size, self._win_size, autoflush=False)
			self._draw_board()

	def _draw_board(self):
		"""
		Draws the board on screen
		Returns: None

		"""
		scale = (self._win_size - 20) / self._size
		top_left = Point(10, 10)
		bottom_right = Point(self._win_size - 10, self._win_size - 10)
		rect = Rectangle(top_left, bottom_right)
		assert (self._size > 1)
		for x in range(1, self._size):
			ratio = (self._win_size - 20) / self._size
			# Horizontal line
			hor = Line(Point(10 + ratio * x, 10), Point(10 + ratio * x, self._win_size - 10))
			# Vertical line
			vert = Line(Point(10, 10 + ratio * x), Point(self._win_size - 10, 10 + ratio * x))
			hor.draw(self._win)
			vert.draw(self._win)
		rect.draw(self._win)
		inside_offset = (self._win_size - 20) / (self._size * 2)
		# Draw background squares and tile numbers
		for i in range(0, self._size ** 2, self._size):
			for j in range(self._size):
				r = Rectangle(Point(10 + j * scale, 10 + (i // self._size) * scale),
				              Point(10 + j * scale + 2 * inside_offset,
				                    10 + (i // self._size) * scale + 2 * inside_offset))
				r.setFill(color_rgb(self._board[i + j] * 14, 100, 100))
				r.draw(self._win)
				if 2 ** self._board[i + j] == 1:
					continue
				t = Text(Point(10 + j * scale + inside_offset, 10 + (i // self._size) * scale + inside_offset),
				         2 ** self._board[i + j])
				t.setSize(20)
				t.draw(self._win)

	def _check_end(self) -> None:
		end = True
		for i in range(self._size ** 2):
			end = not ((self._board[i] == 0) or (
					(i + 1) % self._size != 0 and self._board[i] == self._board[i + 1]) or (
					           i + self._size < self._size ** 2 and self._board[i] == self._board[i + self._size]))
			if end is False:
				break

		self.game_ended = end

	# if end:
	# 	board_log.log(logging.INFO, "Game ended")

	def _spawn_piece(self):
		"""
		Spawns a piece on the board. A 2 with probability 0.9 and 4 with probability 0.1
		Returns: None
		"""
		avail = [x for x in range(len(self._board)) if self._board[x] == 0]
		self._board[random.choice(avail)] = np.random.choice([1, 2], p=[0.9, 0.1])

	# board_log.log(logging.DEBUG, str("Spawned value " + str(2 ** val) + " on grid " + str(loc)))
	# board_log.log(logging.DEBUG, "Current board: " + str(self._board))

	def _combiner(self, arange):
		"""
		Combines numbers along range, propagates out from start.
		Args:
			arange: Range to combine along

		Returns: Whether or not any tiles changed position (boolean)

		"""
		moved = False
		prev = 0
		for i in range(1, len(arange)):
			if self._board[arange[i]] != 0:
				# Can combine in direction of swipe
				if self._board[arange[prev]] == self._board[arange[i]]:
					self._board[arange[prev]] += 1
					self._board[arange[i]] = 0
					prev += 1
					moved = True
				# Can't combine (or zero)
				elif self._board[arange[prev]] != self._board[arange[i]]:
					# Zero
					if self._board[arange[prev]] != 0:
						prev += 1
						if prev == i:
							continue
					self._board[arange[prev]] = self._board[arange[i]]
					self._board[arange[i]] = 0
					moved = True
		return moved

	def _on_press(self, key):
		"""
		Event handler for keyboard. Used in interactive mode
		Args:
			key: Key that has been pressed

		Returns: Nothing

		"""
		try:
			if key == keyboard.Key.right:
				# swipe right
				self.swipe_right()
			elif key == keyboard.Key.left:
				# swipe left
				self.swipe_left()
			elif key == keyboard.Key.up:
				# swipe up
				self.swipe_up()
			elif key == keyboard.Key.down:
				# swipe down
				self.swipe_down()
			else:
				self._key_listener.stop()
				self._win.close()
		except AttributeError:
			self._key_listener.stop()
			self._win.close()

	def _on_release(self, key):
		"""
		Event handler for keyboard. Used in interactive mode
		Args:
			key: Key that has been pressed

		Returns: Nothing

		"""
		pass

	def swipe_left(self) -> int:
		"""
		Moves pieces to the left
		Returns: 0 on success, 1 otherwise
		"""
		board_log.log(logging.DEBUG, "Swipe left")
		moved = False
		for i in range(0, self._size ** 2, self._size):
			arange = range(i, self._size + i)
			moved = self._combiner(arange) or moved
		if moved:
			self._spawn_piece()
			self._check_end()
			return 0
		else:
			return 1

	def swipe_right(self) -> int:
		"""
		Moves pieces to the right
		Returns: 0 on success, 1 otherwise
		"""
		# board_log.log(logging.DEBUG, "Swipe right")
		moved = False
		for i in range(self._size - 1, self._size ** 2, self._size):
			arange = range(i, i - self._size, -1)
			moved = self._combiner(arange) or moved
		if moved:
			self._spawn_piece()
			self._check_end()
			return 0
		else:
			return 1

	def swipe_up(self) -> int:
		"""
		Moves pieces up
		Returns: 0 on success, 1 otherwise

		"""
		# board_log.log(logging.DEBUG, "Swipe up")
		moved = False
		for i in range(0, self._size, 1):
			arange = range(i, self._size ** 2, self._size)
			moved = self._combiner(arange) or moved
		if moved:
			self._spawn_piece()
			self._check_end()
			return 0
		else:
			return 1

	def swipe_down(self) -> int:
		"""
		Moves pieces down
		Returns: 0 on success, 1 otherwise

		"""
		# board_log.log(logging.DEBUG, "Swipe down")
		moved = False
		for i in range((self._size - 1) * self._size, self._size ** 2, 1):
			arange = range(i, -1, -self._size)
			moved = self._combiner(arange) or moved
		if moved:
			self._spawn_piece()
			self._check_end()
			return 0
		else:
			return 1

	def start_interactive(self):
		"""
		Starts 2048 in interactive mode.
		Returns: Nothing
		"""
		# Blocking event listener
		self._key_listener.start()
		while self._key_listener.running:
			for item in self._win.items[:]:
				item.undraw()
			self._draw_board()
			update(15)

	def update_graphics(self):
		"""
		Used for forcing graphic updates
		Returns: None

		"""
		for item in self._win.items[:]:
			item.undraw()
		self._draw_board()
		self._win.flush()
