import random
import pygame
import pickle

WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}
light_col = (241, 217, 181)
dark_col = (181, 136, 99)


# Call this once to populate IMAGES dictionary
def load_images():
    piece_names = ['wp', 'wN', 'wB', 'wK', 'wR', 'wQ', 'bp', 'bN', 'bB', 'bK', 'bR', 'bQ']
    for piece in piece_names:
        # Add to dictionary and scale to match square size
        IMAGES[piece] = pygame.transform.scale(pygame.image.load(piece + ".png"), (SQ_SIZE, SQ_SIZE))


def rook_squares():
    rook_squares = {}

    for row in range(0, 8):
        for col in range(0, 8):
            # Keep list of each direction for a given (row,col)
            north_moves = []
            east_moves = []
            south_moves = []
            west_moves = []

            for x in range(1, 8):
                north = (row + x, col)
                if north[0] in range(0, 8):
                    north_moves.append(north)
                else:
                    break

            for x in range(1, 8):
                east = (row, col + x)
                if east[1] in range(0, 8):
                    east_moves.append(east)
                else:
                    break

            for x in range(1, 8):
                south = (row - x, col)
                if south[0] in range(0, 8):
                    south_moves.append(south)
                else:
                    break

            for x in range(1, 8):
                west = (row, col - x)
                if west[1] in range(0, 8):
                    west_moves.append(west)
                else:
                    break

            rook_squares[(row, col)] = [north_moves, east_moves, south_moves, west_moves]

    return rook_squares


print(rook_squares())


def bishop_squares():
    bishop_squares = {}

    for row in range(0, 8):
        for col in range(0, 8):
            # Keep list of each direction for a given (row,col)
            north_east_moves = []
            south_east_moves = []
            south_west_moves = []
            north_west_moves = []

            for x in range(1, 8):
                north_east = (row - x, col + x)
                if north_east[0] in range(0, 8) and north_east[1] in range(0, 8):
                    north_east_moves.append(north_east)
                else:
                    break

            for x in range(1, 8):
                south_east = (row + x, col + x)
                if south_east[0] in range(0, 8) and south_east[1] in range(0, 8):
                    south_east_moves.append(south_east)
                else:
                    break

            for x in range(1, 8):
                south_west = (row + x, col - x)
                if south_west[0] in range(0, 8) and south_west[1] in range(0, 8):
                    south_west_moves.append(south_west)
                else:
                    break

            for x in range(1, 8):
                north_west = (row - x, col - x)
                if north_west[0] in range(0, 8) and north_west[1] in range(0, 8):
                    north_west_moves.append(north_west)
                else:
                    break

            bishop_squares[(row, col)] = [north_east_moves, south_east_moves, south_west_moves, north_west_moves]

    return bishop_squares


def knight_squares():
    knight_squares = {}

    for row in range(0, 8):
        for col in range(0, 8):
            move_list = []
            n_moves = [[2, 1], [2, -1], [-2, 1], [-2, -1], [1, 2], [-1, 2], [1, -2], [-1, -2]]
            for item in n_moves:
                new_pos = (row + item[0], col + item[1])
                if new_pos[0] in range(0, 8) and new_pos[1] in range(0, 8):
                    move_list.append(new_pos)

            knight_squares[(row, col)] = move_list
    return knight_squares


def king_squares():
    king_squares = {}

    for row in range(0, 8):
        for col in range(0, 8):
            move_list = []
            n_moves = [[1, -1], [1, 0], [1, 1], [0, -1], [0, 1], [-1, -1], [-1, 0], [-1, 1]]
            for item in n_moves:
                new_pos = (row + item[0], col + item[1])
                if new_pos[0] in range(0, 8) and new_pos[1] in range(0, 8):
                    move_list.append(new_pos)

            king_squares[(row, col)] = move_list
    return king_squares


def queen_squares():
    queen_squares = {}
    rooks = rook_squares()
    bishops = bishop_squares()

    for row in range(0, 8):
        for col in range(0, 8):
            queen_moves = rooks[(row, col)]
            queen_moves.extend(bishops[(row, col)])
            queen_squares[(row, col)] = queen_moves

    return queen_squares


'''
Saved squares available to a piece in any particular position.
Should be initialized at start-up
'''
rooks = rook_squares()
bishops = bishop_squares()
knights = knight_squares()
queens = queen_squares()
kings = king_squares()

values = {'p': 10, 'N': 30, 'B': 30, 'K': 40, 'R': 50, 'Q': 90}


class Piece:

    def __init__(self, colour, kind, position):
        self.colour = colour
        self.kind = kind
        self.position = position

        self.value = values[kind]  # A piece's intrinsic value
        self.move_count = 0

        # only for kings
        self.castled = False

        self.attacks = []  # This contains a list of piece values attacking this piece
        self.defences = []  # This contains a list of piece values defending this piece
        self.hidden_attacks = 0  # This contains the number of discovered attacks by lesser pieces (applied if piece is defended)
        self.hidden_targets = 0  # All possible discovered attacks (applied if piece is un-defended)

    def piece_score(self):
        final_piece_score = self.value  # Initially, the piece has a score equal to it's value

        # Evaluate hidden attacks first
        if self.kind == 'K':  # Discovered check
            final_piece_score -= 0.3 * self.value * self.hidden_targets
        elif len(self.defences) == 0:  # Discovered attack on unprotected piece
            final_piece_score -= 0.05 * self.value * self.hidden_targets
        else:  # Discovered attack on any piece
            final_piece_score -= 0.02 * self.value * self.hidden_attacks

        if len(self.attacks) == 0:
            return final_piece_score

        # Only continue if piece is being attacked

        a = self.attacks
        d = self.defences
        a.sort()
        d.sort()

        # Unprotected piece under attack
        if len(d) == 0 and len(a) > 0:
            final_piece_score -= 0.1 * self.value
            return final_piece_score

        # Piece attacked by lesser piece
        if a[0] < self.value:
            final_piece_score -= 0.1 * self.value
            return final_piece_score

        '''
        To simulate trading on this square:
        '''
        move_num = 0
        occupied_value = self.value  # Initially this piece occupies the square
        while True:
            if len(a) == 0:
                break

            if len(d) == 0:
                final_piece_score -= 0.1 * self.value
                break

            if move_num % 2 == 0:  # If it is the attackers hypothetical move
                if a[0] < occupied_value or a[0] < d[0]:  # Take if winning
                    occupied_value = a[0]
                    a.pop(0)
                    move_num += 1
                    continue
                else:
                    break
            elif move_num % 2 == 1:  # If it is the defenders hypothetical move
                if d[0] < occupied_value or d[0] < a[0]:  # Take if winning
                    occupied_value = d[0]
                    d.pop(0)
                    move_num += 1
                    continue
                else:
                    final_piece_score -= 0.1 * self.value
                    break

        return final_piece_score

    def get_string(self):
        return self.colour + self.kind

    def __str__(self):
        score = self.piece_score()
        return self.colour + self.kind + "\n" + "attacks = " + str(self.attacks) + "\n" + "defences = " + str(
            self.defences) + "\n" + "hidden targets = " + str(self.hidden_targets) + "\n" + "hidden attacks = " + str(
            self.hidden_attacks) + '\n' + "value: " + str(score)


class Board:

    def __init__(self, board):
        self.board = board
        self.last_few_positions = [[0], [1], [2], [3], [4], [5], [6], [7], [8]]
        self.previous_move = ["", [], []]
        self.check = {'w': False, 'b': False}
        self.white_king = (7, 4)
        self.black_king = (0, 4)
        self.team_moves = {'w': [], 'b': []}
        self.legal_moves = {'w': {}, 'b': {}}
        self.piece_dicts = {}
        self.graveyard = []
        self.move_count = 0

    def get_piece(self, pos):
        return self.board[pos[0]][pos[1]]

    def get_king(self, col):
        for row in self.board:
            for square in row:
                if square != '--':
                    if square.get_string() == 'wK':
                        self.white_king = square
                        if col == 'w':
                            return square
                    elif square.get_string() == 'bK':
                        self.black_king = square
                        if col == 'b':
                            return square

    def populate_dicts(self):
        for row in range(8):
            for col in range(8):
                square = self.get_piece((row, col))
                if square != '--':
                    self.piece_dicts[(row, col)] = square

    def piece_count(self):
        p_count = 0
        for row in self.board:
            for square in row:
                if square != '--':
                    p_count += 1
        return p_count

    def draw_board(self, screen, highlights, sq_selected):
        colours = [pygame.Color(light_col), pygame.Color(dark_col)]
        for r in range(DIMENSION):
            for c in range(DIMENSION):
                colour = colours[((r + c) % 2)]
                pygame.draw.rect(screen, colour, pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
                square = self.board[r][c]
                if highlights:
                    if (r, c) in highlights:
                        if self.board[r][c] != '--':
                            filled = pygame.Surface((SQ_SIZE, SQ_SIZE))
                            filled.set_alpha(100)
                            filled.fill(pygame.Color("green"))
                            screen.blit(filled, (c * SQ_SIZE, r * SQ_SIZE))
                        else:
                            empty = pygame.Surface((SQ_SIZE, SQ_SIZE))
                            empty.set_alpha(60)
                            empty.fill(pygame.Color("green"))
                            screen.blit(empty, (c * SQ_SIZE, r * SQ_SIZE))
                if ((r, c) == sq_selected) or ((r, c) == self.previous_move[1] or (r, c) == self.previous_move[
                    2]):  # Highlight selected square and previous moves yellow
                    filled = pygame.Surface((SQ_SIZE, SQ_SIZE))
                    filled.set_alpha(30)
                    filled.fill(pygame.Color("yellow"))
                    screen.blit(filled, (c * SQ_SIZE, r * SQ_SIZE))
                if (self.check['w'] == True and (r, c) == self.white_king) or (
                        self.check['b'] == True and (r, c) == self.black_king):  # Highlight king red if in check
                    filled = pygame.Surface((SQ_SIZE, SQ_SIZE))
                    filled.set_alpha(60)
                    filled.fill(pygame.Color("red"))
                    screen.blit(filled, (c * SQ_SIZE, r * SQ_SIZE))
                if square != '--':  # Populate board with piece images
                    piece = square.get_string()
                    screen.blit(IMAGES[piece], pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

    def board_string(self):
        disp_board = [['--' for i in range(8)] for i in range(8)]
        for row in range(8):
            for col in range(8):
                if self.get_piece((row, col)) == '--':
                    pass
                else:
                    disp_board[row][col] = self.get_piece((row, col)).get_string()
                    # disp_board[row][col] = self.get_piece((row, col)).at_risk
        return disp_board

    def __str__(self):
        disp_board = self.board_string()
        board_str = ''
        for row in disp_board:
            board_str += str(row) + '\n'
        return board_str


def board_val(game_board):
    center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
    w_piece_count = 0
    b_piece_count = 0
    w_central = 0
    b_central = 0
    score = 0
    for col in ['w', 'b']:
        end_game_score = end_game(game_board, col)
        if end_game_score[0]:
            if col == 'w':
                score = -1000000
            else:
                score = 1000000
            return score

    if game_board.last_few_positions[0] == game_board.last_few_positions[4] and game_board.last_few_positions[4] == \
            game_board.last_few_positions[8]:
        if game_board.last_few_positions[8][1][0].colour == 'w':
            score -= 10000
        if game_board.last_few_positions[8][1][0].colour == 'b':
            score += 10000

    # Sum piece values
    # reward central positioning (2 points)
    # reward passive King play ()
    for row in game_board.board:
        for square in row:
            if square != '--':

                if square.colour == 'w':
                    try:
                        mobility = len(game_board.legal_moves['w'][square])
                    except:
                        mobility = 0
                    w_piece_count += 1
                    score += square.piece_score()
                    score += 0.1 * mobility
                    if square.position in center_squares:
                        w_central += 1
                    if square.kind == 'K':
                        if square.position[0] in [7, 6]:
                            score += 1
                        if square.move_count == 0:
                            score += 1.5
                        if square.castled:
                            score += 5

                elif square.colour == 'b':
                    try:
                        mobility = len(game_board.legal_moves['w'][square])
                    except:
                        mobility = 0
                    score -= square.piece_score()
                    score -= 0.1 * mobility
                    b_piece_count += 1
                    if square.position in center_squares:
                        b_central += 1
                    if square.kind == 'K':
                        if square.position[0] in [0, 1]:
                            score -= 1
                        if square.move_count == 0:
                            score -= 1.5
                        if square.castled:
                            score -= 5

    if w_piece_count > 5:
        score += w_central * 3
    if b_piece_count > 5:
        score -= b_central * 3

    if end_game_score[1]:
        if score > 0:
            score = -1000
        elif score < 0:
            score = 1000

    return score


def board_val_2(game_board):
    score = 0
    center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
    piece_count = {'w': 0, 'b': 0}
    central = {'w': 0, 'b': 0}
    m = {'w': 1, 'b': -1}  # Multiplier used to make black scores opposite of white scores.

    for col in ['w', 'b']:
        if game_board.check[col]:
            if end_game(game_board, col)[0]:
                score = -1000000
                score = score * m[col]
                return score

    if game_board.last_few_positions[0] == game_board.last_few_positions[4] and game_board.last_few_positions[4] == \
            game_board.last_few_positions[8]:
        score = -1000
        score = (m[game_board.last_few_positions[8][1][0].colour]) * score
        return score

    # Sum piece values
    # reward central positioning (2 points)
    # reward passive King play ()

    # for loc, piece in game_board.piece_dicts.items():
    for row in game_board.board:
        for square in row:
            if square != '--':
                p_col = square.colour
                piece_count[p_col] += 1
                score += m[p_col] * square.value
                if square.position in center_squares:
                    central[p_col] += 1
                if square.castled:
                    score += m[col] * 20

    if piece_count['w'] > 6:
        score += central['w'] * 5
    elif piece_count['b'] > 6:
        score -= central['b'] * 5

    return score


def get_board_data(game_board):
    last_few_positions = pickle.loads(pickle.dumps(game_board.last_few_positions))
    # last_few_positions = game_board.last_few_positions
    previous_move = pickle.loads(pickle.dumps(game_board.previous_move))
    # previous_move = game_board.previous_move
    check = game_board.check
    white_king = game_board.white_king
    black_king = game_board.black_king
    team_moves = game_board.team_moves
    legal_moves = pickle.loads(pickle.dumps(game_board.legal_moves))

    board_data = {"last_few_positions": last_few_positions, "previous_move": previous_move, "check": check,
                  "white_king": white_king, "black_king": black_king, "team_moves": team_moves,
                  "legal_moves": legal_moves}

    return board_data


def import_board_data(game_board, board_data, piece_moved, initial_pos):
    reverse_move(game_board, piece_moved, initial_pos)

    game_board.last_few_positions = board_data["last_few_positions"]
    game_board.previous_move = board_data["previous_move"]
    game_board.check = board_data["check"]
    game_board.white_king = board_data["white_king"]
    game_board.black_king = board_data["black_king"]
    game_board.team_moves = board_data["team_moves"]
    game_board.legal_moves = board_data["legal_moves"]


def in_check(game_board, col):
    check = False
    if col == 'w':
        if game_board.white_king in game_board.team_moves['b']:
            check = True
            return check
    elif col == 'b':
        if game_board.black_king in game_board.team_moves['w']:
            check = True
            return check


def board_setup_normal():
    board_setup = [['--' for i in range(8)] for i in range(8)]

    white_King = Piece('w', 'K', (7, 4))
    white_Queen = Piece('w', 'Q', (7, 3))
    white_Rook_L = Piece('w', 'R', (7, 0))
    white_Rook_R = Piece('w', 'R', (7, 7))

    black_King = Piece('b', 'K', (0, 4))
    black_Queen = Piece('b', 'Q', (0, 3))
    black_Rook_L = Piece('b', 'R', (0, 0))
    black_Rook_R = Piece('b', 'R', (0, 7))

    # Initiate Rooks
    board_setup[7][0] = white_Rook_L
    board_setup[7][7] = white_Rook_R
    board_setup[0][0] = black_Rook_L
    board_setup[0][7] = black_Rook_R

    # Initiate Queens and Kings
    board_setup[7][3] = white_Queen
    board_setup[7][4] = white_King
    board_setup[0][3] = black_Queen
    board_setup[0][4] = black_King

    for col, flip in [['w', 0], ['b', 7]]:
        # Initiate Knights
        board_setup[7 - flip][1] = Piece(col, 'N', (7 - flip, 1))
        board_setup[7 - flip][6] = Piece(col, 'N', (7 - flip, 6))

        # Initiate Bishops
        board_setup[7 - flip][2] = Piece(col, 'B', (7 - flip, 2))
        board_setup[7 - flip][5] = Piece(col, 'B', (7 - flip, 5))

        # Initiate pawns
    for col, flip in [['w', 0], ['b', 5]]:
        for x in range(0, 8):
            board_setup[6 - flip][x] = Piece(col, 'p', (6 - flip, x))

    return board_setup


def board_setup_test():
    board_setup = [['--' for i in range(8)] for i in range(8)]

    white_King = Piece('w', 'K', (7, 4))
    white_Queen = Piece('w', 'Q', (7, 3))
    white_Rook_L = Piece('w', 'R', (7, 0))
    white_Rook_R = Piece('w', 'R', (7, 7))

    black_King = Piece('b', 'K', (0, 4))
    # black_Queen = Piece('b', 'Q', (0, 3))
    # black_Rook_L = Piece('b', 'R', (0, 0))
    # black_Rook_R = Piece('b', 'R', (0, 7))

    # Initiate Rooks
    board_setup[7][0] = white_Rook_L
    board_setup[7][7] = white_Rook_R
    # board_setup[0][0] = black_Rook_L
    # board_setup[0][7] = black_Rook_R

    # Initiate Queens and Kings
    board_setup[7][3] = white_Queen
    board_setup[7][4] = white_King
    # board_setup[0][3] = black_Queen
    board_setup[0][4] = black_King

    board_setup[6][1] = Piece('w', 'p', (6, 1))

    return board_setup


def reverse_move(game_board, piece, dest):
    piece.move_count -= 1
    vacant_pos = piece.position

    # Empty piece_dicts location and temporarily empty square
    game_board.board[vacant_pos[0]][vacant_pos[1]] = '--'
    game_board.piece_dicts.pop(vacant_pos, None)

    # Check for pawn promotion
    if game_board.previous_move[0] == 'wp' and game_board.previous_move[2][0] == 0:
        vacant_pos = game_board.previous_move[2]
        game_board.board[vacant_pos[0]][vacant_pos[1]] = '--'
        game_board.piece_dicts.pop(vacant_pos, None)
        new_pawn = Piece('w', 'p', dest)
        game_board.board[dest[0]][dest[1]] = new_pawn
        game_board.piece_dicts[dest] = new_pawn
    elif game_board.previous_move[0] == 'bp' and game_board.previous_move[2][0] == 7:
        vacant_pos = game_board.previous_move[2]
        game_board.board[vacant_pos[0]][vacant_pos[1]] = '--'
        game_board.piece_dicts.pop(vacant_pos, None)
        new_pawn = Piece('b', 'p', dest)
        game_board.board[dest[0]][dest[1]] = new_pawn
        game_board.piece_dicts[dest] = new_pawn
    else:
        # Empty piece_dicts location and temporarily empty square
        game_board.board[vacant_pos[0]][vacant_pos[1]] = '--'
        game_board.piece_dicts.pop(vacant_pos, None)
        # Move piece back to original square
        game_board.board[dest[0]][dest[1]] = piece
        piece.position = dest
        game_board.piece_dicts[dest] = piece

    # Check for castling
    if piece.get_string() == 'wK' and vacant_pos == (7, 2) and dest == (7, 4):
        piece.castled = False
        reverse_move(game_board, game_board.board[7][3], (7, 0))
        game_board.move_count += 1  # To counteract move_count reduction by moving castle
    elif piece.get_string() == 'wK' and vacant_pos == (7, 6) and dest == (7, 4):
        piece.castled = False
        reverse_move(game_board, game_board.board[7][5], (7, 7))
        game_board.move_count += 1  # To counteract move_count reduction by moving castle
    elif piece.get_string() == 'bK' and vacant_pos == (0, 2) and dest == (0, 4):
        piece.castled = False
        reverse_move(game_board, game_board.board[0][3], (0, 0))
        game_board.move_count += 1  # To counteract move_count reduction by moving castle
    elif piece.get_string() == 'bK' and vacant_pos == (0, 6) and dest == (0, 4):
        reverse_move(game_board, game_board.board[0][5], (0, 7))
        piece.castled = False
        game_board.move_count += 1  # To counteract move_count reduction by moving castle

    # En passant only happens when a piece has been taken
    if len(game_board.graveyard) > 0:
        revive = game_board.graveyard[-1]

        # Check if the most recent dead piece died in the last move
        if revive[0] == game_board.move_count:
            # White en-passant reversal
            if piece.get_string() == 'wp' and vacant_pos == (dest[0] - 1, dest[1] + 1) and revive[1] == (
                    dest[0], dest[1] + 1):
                game_board.piece_dicts[(dest[0], dest[1] + 1)] = revive[2]
                game_board.board[dest[0]][dest[1] + 1] = revive[2]
                game_board.graveyard.pop()
            elif piece.get_string() == 'wp' and vacant_pos == (dest[0] - 1, dest[1] - 1) and revive[1] == (
                    dest[0], dest[1] - 1):
                game_board.piece_dicts[(dest[0], dest[1] - 1)] = revive[2]
                game_board.board[dest[0]][dest[1] - 1] = revive[2]
                game_board.graveyard.pop()

            # Black en-passant reversal
            elif piece.get_string() == 'bp' and vacant_pos == (dest[0] + 1, dest[1] - 1) and revive[1] == (
                    dest[0], dest[1] - 1):
                game_board.piece_dicts[(dest[0], dest[1] - 1)] = revive[2]
                game_board.board[dest[0]][dest[1] - 1] = revive[2]
                game_board.graveyard.pop()

            elif piece.get_string() == 'bp' and vacant_pos == (dest[0] + 1, dest[1] + 1) and revive[1] == (
                    dest[0], dest[1] + 1):
                game_board.piece_dicts[(dest[0], dest[1] + 1)] = revive[2]
                game_board.board[dest[0]][dest[1] + 1] = revive[2]
                game_board.graveyard.pop()

            # Any other move
            elif revive[1] == vacant_pos:
                game_board.piece_dicts[vacant_pos] = revive[2]
                game_board.board[vacant_pos[0]][vacant_pos[1]] = revive[2]
                game_board.graveyard.pop()

    game_board.move_count -= 1  # Reduce the move_count by 1


'''
Makes a move on the board, including castling and pawn promotion/
Updates piece locations and move-count
'''


def make_move(game_board, piece, dest):
    # Update board history
    game_board.previous_move = [piece.get_string(), piece.position, dest]
    game_board.last_few_positions.append([game_board.board_string(), (piece, dest)])
    game_board.last_few_positions.pop(0)
    game_board.move_count += 1

    if piece.get_string() == 'wK':
        game_board.white_king = dest
    elif piece.get_string() == 'bK':
        game_board.black_king = dest
    # Increase move count for piece
    piece.move_count += 1

    # Empty starting square
    start = piece.position
    game_board.board[start[0]][start[1]] = '--'
    game_board.piece_dicts.pop(start, None)

    try:
        take_piece = game_board.piece_dicts[
            dest]  # Delete the piece that was in the destination key of the dict (if any)
    except:
        pass
    else:
        game_board.graveyard.append([game_board.move_count, dest, take_piece])
        game_board.piece_dicts.pop(dest, None)

        # Promote pawns to queens if possible
    if piece.get_string() == 'wp' and dest[0] == 0:
        new_queen = Piece('w', 'Q', dest)
        game_board.board[dest[0]][dest[1]] = new_queen
        game_board.piece_dicts[dest] = new_queen  # Add the piece to the piece_dicts in it's new position

    elif piece.get_string() == 'bp' and dest[0] == 7:
        new_queen = Piece('b', 'Q', dest)
        game_board.board[dest[0]][dest[1]] = new_queen
        game_board.piece_dicts[dest] = new_queen  # Add the piece to the piece_dicts in it's new position

    # White En passant moves
    elif piece.get_string() == 'wp' and dest == (start[0] - 1, start[1] + 1) and game_board.get_piece(dest) == '--':
        game_board.board[dest[0]][dest[1]] = piece
        piece.position = dest
        game_board.board[start[0]][start[1] + 1] = '--'
        try:
            take_piece = game_board.piece_dicts[(start[0], start[1] + 1)]  # Delete the piece that got killed
        except:
            pass
        else:
            game_board.graveyard.append([game_board.move_count, (start[0], start[1] + 1), take_piece])
            game_board.piece_dicts.pop((start[0], start[1] + 1), None)
        game_board.piece_dicts[dest] = piece  # Add the piece to the piece_dicts in it's new position

    elif piece.get_string() == 'wp' and dest == (start[0] - 1, start[1] - 1) and game_board.get_piece(dest) == '--':
        game_board.board[dest[0]][dest[1]] = piece
        piece.position = dest
        game_board.board[start[0]][start[1] - 1] = '--'
        try:
            take_piece = game_board.piece_dicts[(start[0], start[1] - 1)]  # Delete the piece that got killed
        except:
            pass
        else:
            game_board.graveyard.append([game_board.move_count, (start[0], start[1] - 1), take_piece])
            game_board.piece_dicts.pop((start[0], start[1] - 1), None)
        game_board.piece_dicts[dest] = piece  # Add the piece to the piece_dicts in it's new position

    # Black En passant moves

    elif piece.get_string() == 'bp' and dest == (start[0] + 1, start[1] + 1) and game_board.get_piece(dest) == '--':
        game_board.board[dest[0]][dest[1]] = piece
        piece.position = dest
        game_board.board[start[0]][start[1] + 1] = '--'
        try:
            take_piece = game_board.piece_dicts[(start[0], start[1] + 1)]  # Delete the piece that got killed
        except:
            pass
        else:
            game_board.graveyard.append([game_board.move_count, (start[0], start[1] + 1), take_piece])
            game_board.piece_dicts.pop((start[0], start[1] + 1), None)

        game_board.piece_dicts[dest] = piece  # Add the piece to the piece_dicts in it's new position

    elif piece.get_string() == 'bp' and dest == (start[0] + 1, start[1] - 1) and game_board.get_piece(dest) == '--':
        game_board.board[dest[0]][dest[1]] = piece
        piece.position = dest
        game_board.board[start[0]][start[1] - 1] = '--'
        try:
            take_piece = game_board.piece_dicts[(start[0], start[1] - 1)]  # Delete the piece that got killed
        except:
            pass
        else:
            game_board.graveyard.append([game_board.move_count, (start[0], start[1] - 1), take_piece])
            game_board.piece_dicts.pop((start[0], start[1] - 1), None)
        game_board.piece_dicts[dest] = piece  # Add the piece to the piece_dicts in it's new position

    # Check for white queen-side castling
    elif piece.get_string() == 'wK' and start == (7, 4) and dest == (7, 2):
        piece.castled = True
        # Move King
        game_board.board[dest[0]][dest[1]] = piece
        piece.position = dest
        # Move Rook
        game_board.get_piece((7, 0)).move_count += 1
        w_rook_L = game_board.get_piece((7, 0))
        game_board.board[7][0] = '--'
        game_board.board[7][3] = w_rook_L
        w_rook_L.position = (7, 3)

        try:
            del game_board.piece_dicts[(7, 0)]  # Delete the old rook position
        except:
            pass
        game_board.piece_dicts[(7, 3)] = w_rook_L  # Add the piece to the piece_dicts in it's new position
        game_board.piece_dicts[dest] = piece  # Add the piece to the piece_dicts in it's new position

    # Check for white King-side castling
    elif piece.get_string() == 'wK' and start == (7, 4) and dest == (7, 6):
        piece.castled = True
        # Move King
        game_board.board[dest[0]][dest[1]] = piece
        piece.position = dest
        # Move Rook
        game_board.get_piece((7, 7)).move_count += 1
        w_rook_R = game_board.get_piece((7, 7))
        game_board.board[7][7] = '--'
        game_board.board[7][5] = w_rook_R
        w_rook_R.position = (7, 5)

        try:
            del game_board.piece_dicts[(7, 7)]  # Delete the old rook position
        except:
            pass
        game_board.piece_dicts[(7, 5)] = w_rook_R  # Add the piece to the piece_dicts in it's new position
        game_board.piece_dicts[dest] = piece  # Add the piece to the piece_dicts in it's new position

    # Check for black queen-side castling
    elif piece.get_string() == 'bK' and start == (0, 4) and dest == (0, 2):
        piece.castled = True
        # Move King
        game_board.board[dest[0]][dest[1]] = piece
        piece.position = dest
        # Move Rook
        game_board.get_piece((0, 0)).move_count += 1
        b_rook_L = game_board.get_piece((0, 0))
        game_board.board[0][0] = '--'
        game_board.board[0][3] = b_rook_L
        b_rook_L.position = (0, 3)

        try:
            del game_board.piece_dicts[(0, 0)]  # Delete the old rook position
        except:
            pass
        game_board.piece_dicts[(0, 3)] = b_rook_L  # Add the piece to the piece_dicts in it's new position
        game_board.piece_dicts[dest] = piece  # Add the piece to the piece_dicts in it's new position

    # Check for black King-side castling
    elif piece.get_string() == 'bK' and start == (0, 4) and dest == (0, 6):
        piece.castled = True
        # Move King
        game_board.board[dest[0]][dest[1]] = piece
        piece.position = dest
        # Move Rook
        game_board.get_piece((0, 7)).move_count += 1
        b_rook_R = game_board.get_piece((0, 7))
        game_board.board[0][7] = '--'
        game_board.board[0][5] = b_rook_R
        b_rook_R.position = (0, 5)

        try:
            del game_board.piece_dicts[(0, 7)]  # Delete the old rook position
        except:
            pass
        game_board.piece_dicts[(0, 5)] = b_rook_R  # Add the piece to the piece_dicts in it's new position
        game_board.piece_dicts[dest] = piece  # Add the piece to the piece_dicts in it's new position

    # For normal takes
    else:
        game_board.board[dest[0]][dest[1]] = piece
        piece.position = dest
        game_board.piece_dicts[dest] = piece


'''
Creates a copy of a board after a piece is moved
get_piece is used so that the piece object moved is the one in the copy, not the original board.
'''


def sim_next(game_board, piece, dest):
    x = piece.position
    test_board = pickle.loads(pickle.dumps(game_board))
    make_move(test_board, test_board.get_piece(x), dest)

    return test_board


'''
Gets all moves for a piece (ignoring self-checking) up to when it can take a piece or hits own colour

'''


def get_moves(game_board, piece):
    possible_moves = []

    own_colour = piece.colour

    colours = ['w', 'b']

    other_col = colours[1 - colours.index(own_colour)]

    # Use pre-determined squares for rook, bishop and queen moves
    if piece.kind in ['R', 'B', 'Q']:
        if piece.kind == 'R':
            move_list = rooks[piece.position]
        elif piece.kind == 'B':
            move_list = bishops[piece.position]
        elif piece.kind == 'Q':
            move_list = queens[piece.position]

        for direction in move_list:
            if len(direction) > 0:
                counting = True
                for step in direction:
                    destination_square = game_board.get_piece(step)
                    if counting == True:
                        if destination_square == '--':
                            possible_moves.append(step)

                        elif destination_square.colour == own_colour:  # If you hit your own team (defend)
                            counting = False
                            destination_square.defences.append(piece.value)

                        else:  # If you hit the other team colour
                            destination_square.attacks.append(piece.value)
                            possible_moves.append(step)
                            counting = False
                    else:
                        if game_board.get_piece(step) == '--':
                            continue
                        elif game_board.get_piece(
                                step).colour == own_colour:  # If the discovered attack is your own team, ignore.
                            break
                        else:  # If there is a potential discovered attack
                            destination_square.hidden_targets += 0.2
                            if piece.value < destination_square.value:  # If it is a higher value piece
                                destination_square.hidden_attacks += 1
                            break
    if piece.kind == 'N':
        for dest in knights[piece.position]:
            destination_square = game_board.get_piece(dest)
            if destination_square == '--':
                possible_moves.append(dest)
            elif destination_square.colour != own_colour:
                destination_square.attacks.append(piece.value)
                possible_moves.append(dest)
            elif destination_square.colour == own_colour:
                destination_square.defences.append(piece.value)
            else:
                pass

    if piece.kind == 'p':
        if piece.colour == 'b':
            # Initial double move
            if piece.position[0] == 1:
                pos1 = (2, piece.position[1])
                pos2 = (3, piece.position[1])
                if game_board.get_piece(pos1) == '--':
                    if game_board.get_piece(pos2) == '--':
                        possible_moves.append(pos2)

            # Can the pawn move forward one space?
            forward_square = game_board.get_piece((piece.position[0] + 1, piece.position[1]))
            if forward_square == '--':
                possible_moves.append((piece.position[0] + 1, piece.position[1]))

            # Can the pawn attack right?
            new_pos = (piece.position[0] + 1, piece.position[1] + 1)
            if new_pos[0] in range(8) and new_pos[1] in range(8):
                attack_square = game_board.get_piece(new_pos)
                if attack_square != '--':
                    if attack_square.colour == other_col:
                        attack_square.attacks.append(piece.value)
                        possible_moves.append(new_pos)
                    elif attack_square.colour == own_colour:
                        attack_square.defences.append(piece.value)

            # Can the pawn attack left?
            new_pos = (piece.position[0] + 1, piece.position[1] - 1)
            if new_pos[0] in range(8) and new_pos[1] in range(8):
                attack_square = game_board.get_piece(new_pos)
                if attack_square != '--':
                    if attack_square.colour == other_col:
                        attack_square.attacks.append(piece.value)
                        possible_moves.append(new_pos)
                    elif attack_square.colour == own_colour:
                        attack_square.defences.append(piece.value)

            # En Passant
            if game_board.previous_move[0] == 'wp' and game_board.previous_move[1][0] == 6 and \
                    game_board.previous_move[2][0] == 4 and piece.position[0] == 4:
                if game_board.previous_move[2] == (piece.position[0], piece.position[1] + 1):
                    possible_moves.append((piece.position[0] + 1, piece.position[1] + 1))
                    game_board.get_piece((piece.position[0], piece.position[1] + 1)).attacks.append(piece.value)
                if game_board.previous_move[2] == (piece.position[0], piece.position[1] - 1):
                    possible_moves.append((piece.position[0] + 1, piece.position[1] - 1))
                    game_board.get_piece((piece.position[0], piece.position[1] - 1)).attacks.append(piece.value)

        if piece.colour == 'w':
            # Initial double move
            if piece.position[0] == 6:
                pos1 = (5, piece.position[1])
                pos2 = (4, piece.position[1])
                if game_board.get_piece(pos1) == '--':
                    if game_board.get_piece(pos2) == '--':
                        possible_moves.append(pos2)

            # Can the pawn move forward one space?
            forward_square = game_board.get_piece((piece.position[0] - 1, piece.position[1]))
            if forward_square == '--':
                possible_moves.append((piece.position[0] - 1, piece.position[1]))

            # Can the pawn attack right?
            new_pos = (piece.position[0] - 1, piece.position[1] + 1)
            if new_pos[0] in range(8) and new_pos[1] in range(8):
                attack_square = game_board.get_piece(new_pos)
                if attack_square != '--':
                    if attack_square.colour == other_col:
                        attack_square.attacks.append(piece.value)
                        possible_moves.append(new_pos)
                    elif attack_square.colour == own_colour:
                        attack_square.defences.append(piece.value)

            # Can the pawn attack left?
            new_pos = (piece.position[0] - 1, piece.position[1] - 1)
            if new_pos[0] in range(8) and new_pos[1] in range(8):
                attack_square = game_board.get_piece(new_pos)
                if attack_square != '--':
                    if attack_square.colour == other_col:
                        attack_square.attacks.append(piece.value)
                        possible_moves.append(new_pos)
                    elif attack_square.colour == own_colour:
                        attack_square.defences.append(piece.value)

            # En Passant
            if game_board.previous_move[0] == 'bp' and game_board.previous_move[1][0] == 1 and \
                    game_board.previous_move[2][0] == 3 and piece.position[0] == 3:
                if game_board.previous_move[2] == (piece.position[0], piece.position[1] + 1):
                    possible_moves.append((piece.position[0] - 1, piece.position[1] + 1))
                    game_board.get_piece((piece.position[0], piece.position[1] + 1)).attacks.append(piece.value)
                if game_board.previous_move[2] == (piece.position[0], piece.position[1] - 1):
                    possible_moves.append((piece.position[0] - 1, piece.position[1] - 1))
                    game_board.get_piece((piece.position[0], piece.position[1] - 1)).attacks.append(piece.value)

    if piece.kind == 'K':  # King does not contribute to defending or attacking other pieces (yet)
        # Generate normal king moves
        for dest in kings[piece.position]:
            destination_square = game_board.get_piece(dest)
            if destination_square == '--':
                possible_moves.append(dest)
            elif destination_square.colour != own_colour:
                # destination_square.attacks.append[piece.value]
                possible_moves.append(dest)
            else:
                pass

        # If King and rook hasn't moved, consider possibility of castling
        if own_colour == 'w' and piece.move_count == 0 and game_board.check['w'] == False:
            try:
                game_board.get_piece((7, 0)).move_count == 0
            except:
                pass
            else:
                empty_check = [game_board.get_piece((7, 1)), game_board.get_piece((7, 2)), game_board.get_piece((7, 3))]
                if all(squares == '--' for squares in empty_check):
                    key_squares = {(7, 2), (7, 3), (7, 4)}
                    if (non_king_moves(game_board, other_col) & key_squares):
                        pass
                    else:
                        possible_moves.append((7, 2))

            # elif own_colour == 'w' and piece.move_count == 0:
            try:
                game_board.get_piece((7, 7)).move_count == 0
            except:
                pass
            else:
                empty_check = [game_board.get_piece((7, 5)), game_board.get_piece((7, 6))]
                if all(squares == '--' for squares in empty_check):
                    key_squares = {(7, 4), (7, 5), (7, 6)}
                    # if (non_king_moves(game_board, other_col) & key_squares):
                    if key_squares.isdisjoint(set(game_board.team_moves[other_col])) == False:
                        pass
                    else:
                        possible_moves.append((7, 6))

        elif own_colour == 'b' and piece.move_count == 0 and game_board.check['b'] == False:
            try:
                game_board.get_piece((0, 0)).move_count == 0
            except:
                pass
            else:
                empty_check = [game_board.get_piece((0, 1)), game_board.get_piece((0, 2)), game_board.get_piece((0, 3))]
                if all(squares == '--' for squares in empty_check):
                    key_squares = {(0, 2), (0, 3), (0, 4)}
                    if (non_king_moves(game_board, other_col) & key_squares):
                        pass
                    else:
                        possible_moves.append((0, 2))

            # elif own_colour == 'b' and piece.move_count == 0:
            try:
                game_board.get_piece((0, 7)).move_count == 0
            except:
                pass
            else:
                empty_check = [game_board.get_piece((0, 5)), game_board.get_piece((0, 6))]
                if all(squares == '--' for squares in empty_check):
                    key_squares = {(0, 4), (0, 5), (0, 6)}
                    # if (non_king_moves(game_board, other_col) & key_squares):
                    if key_squares.isdisjoint(set(game_board.team_moves[other_col])) == False:
                        pass
                    else:
                        possible_moves.append((0, 6))

    return (possible_moves)


def all_team_moves(game_board):
    team_targets = {'w': [], 'b': []}
    game_board.check['w'] = False
    game_board.check['b'] = False

    # Clear piece attribute at_risk
    for square, piece in game_board.piece_dicts.items():
        if piece.get_string() == 'wK':
            game_board.white_king = square
        elif piece.get_string() == 'bK':
            game_board.black_king = square

        piece.attacks = []  # This contains a list of piece values attacking this piece
        piece.defences = []  # This contains a list of piece values defending this piece
        piece.hidden_attacks = 0  # This contains the number of discovered attacks by lesser pieces (applied if piece is defended)
        piece.hidden_targets = 0  # All possible discovered attacks (applied if piece is un-defended)

    for square, piece in game_board.piece_dicts.items():

        if piece.colour == 'w':
            moves = get_moves(game_board, piece)
            team_targets['w'].extend(moves)
        elif piece.colour == 'b':
            moves = get_moves(game_board, piece)
            team_targets['b'].extend(moves)

    if game_board.black_king in team_targets['w']:
        game_board.check['b'] = True
    if game_board.white_king in team_targets['b']:
        game_board.check['w'] = True

    game_board.team_moves = team_targets

    return team_targets


def team_moves(game_board, col):
    team_targets = []
    colours = ['w', 'b']
    other_col = colours[1 - colours.index(col)]

    game_board.check[other_col] = False

    for square, piece in game_board.piece_dicts.items():
        if piece.get_string() == 'wK':
            game_board.white_king = square
        elif piece.get_string() == 'bK':
            game_board.black_king = square
        if piece.colour == col:
            moves = get_moves(game_board, piece)
            team_targets.extend(moves)

    if col == 'w' and game_board.black_king in team_targets:
        game_board.check['b'] = True
    elif col == 'b' and game_board.white_king in team_targets:
        game_board.check['w'] = True
    game_board.team_moves[col] = team_targets

    return team_targets


def full_board_update(game_board):
    team_legal_moves(game_board, 'w')
    team_legal_moves(game_board, 'b')
    all_team_moves(game_board)


def team_legal_moves(game_board, col):
    colours = ['w', 'b']
    other_col = colours[1 - colours.index(col)]
    team_legal_moves = {}

    for row in game_board.board:
        for square in row:
            if square != '--':
                if square.colour == col:
                    initial_moves = get_moves(game_board, square)
                    legal_moves = self_check_adjust(game_board, square, initial_moves)
                    if len(legal_moves) > 0:
                        team_legal_moves[square] = legal_moves

    game_board.legal_moves[col] = team_legal_moves

    return team_legal_moves


# Get list of team attacks to ensure that castling is safe
def non_king_moves(game_board, col):
    attacks = []

    for square, piece in game_board.piece_dicts.items():
        if piece.colour == col and piece.kind != 'K':
            attacks = get_moves(game_board, piece)

    return set(attacks)


def self_check_adjust(game_board, piece, move_list):
    own_colour = piece.colour
    colours = ['w', 'b']
    other_col = colours[1 - colours.index(own_colour)]
    backup = get_board_data(game_board)
    initial_pos = piece.position
    adjusted_list = []
    if len(move_list) > 0:
        for move in move_list:
            make_move(game_board, piece, move)
            team_moves(game_board, other_col)
            if game_board.check[own_colour] == False:
                adjusted_list.append(move)

            import_board_data(game_board, backup, piece, initial_pos)

    return adjusted_list


# NEEDS LEGAL_MOVES[COL] TO BE UPDATED
def end_game(game_board, col):
    endgame = [False, False]

    colours = ['w', 'b']
    other_col = colours[1 - colours.index(col)]

    # Create a list of pieces on board for draw scenarios
    piece_kind_list = []
    # Create a list of pieces for each colour
    pieces = {'w': [], 'b': []}

    for row in game_board.board:
        for square in row:
            if square != '--':
                piece_kind_list.append(square.kind)
                if square.colour == col:
                    pieces[col].append(square)
                else:
                    pieces[other_col].append(square)

    # In both cases there are no legal moves

    # These outcomes result in a draw
    if piece_kind_list == ['K', 'K', 'B'] or piece_kind_list == ['K', 'K', 'N'] or piece_kind_list == ['K', 'K']:
        print('Draw!')
        endgame[1] = True

    # If there are 3 repeated positions then it is a draw
    if game_board.last_few_positions[0] == game_board.last_few_positions[4] and game_board.last_few_positions[4] == \
            game_board.last_few_positions[8]:
        print('Draw by reptition!')
        endgame[1] = True

    enemy_moves = []

    if endgame == [False, False]:

        all_moves = game_board.legal_moves[col]

        if len(all_moves) == 0:
            # enemy_moves = game_board.team_moves[other_col]
            if col == 'w':
                if game_board.white_king in game_board.team_moves['b']:
                    endgame[0] = True
                    return endgame
            elif col == 'b':
                if game_board.black_king in game_board.team_moves['w']:
                    endgame[0] = True
                    return endgame

            endgame[1] = True

    return endgame


def end_screen(screen, text):
    font = pygame.font.SysFont("Helvitca", 32, True, False)
    text_object = font.render(text, False, pygame.Color('Black'))
    text_location = pygame.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH / 2 - text_object.get_width() / 2,
                                                          HEIGHT / 2 - text_object.get_height() / 2)  # Center location of text
    screen.blit(text_object, text_location)


def alpha_beta_algorithm(game_board, col, depth, layer=None, crit_val=None, pruning=True):
    colours = ['w', 'b']
    other_col = colours[1 - colours.index(col)]
    branch = 0
    prune_count = 0
    all_moves = {}
    best_moves = []

    if layer == None:
        layer = depth

    if crit_val == None:
        crit_val = {'w': -10000000, 'b': +10000000}

    if layer == 0:
        val = board_val(game_board)

        return val

    moves = game_board.legal_moves[col]

    for piece, poss_moves in moves.items():
        initial_pos = piece.position
        if len(poss_moves) == 0:
            continue

        if depth == layer and len(moves) == 1 and len(moves[
                                                          piece]) == 1:  # If there is only one available move at depth = level, just return that move. No need to look further.
            return (piece, poss_moves[0])

        for pos_1 in poss_moves:
            branch += 1

            last_board = get_board_data(game_board)
            make_move(game_board, piece, pos_1)
            full_board_update(game_board)
            current_board_val = board_val(game_board)

            if True in end_game(game_board, other_col):
                all_moves[(piece, pos_1)] = current_board_val
                import_board_data(game_board, last_board, piece, initial_pos)
                continue

            if branch > 1 and pruning == True:

                if col == 'w':
                    try:
                        max_val = max(all_moves.values())
                        crit_val[col] = max_val
                    except:
                        crit_val[col] = -10000

                else:
                    try:
                        min_val = min(all_moves.values())
                        crit_val[col] = min_val
                    except:
                        crit_val[col] = 10000

            if branch == 1:
                result = alpha_beta_algorithm(game_board, other_col, depth, layer - 1, crit_val, False)
            else:
                result = alpha_beta_algorithm(game_board, other_col, depth, layer - 1, crit_val, True)

            if pruning == False:
                if result == None:
                    import_board_data(game_board, last_board, piece, initial_pos)
                    continue
                else:
                    all_moves[(piece, pos_1)] = result
                    import_board_data(game_board, last_board, piece, initial_pos)
                    continue

            # When pruning == True, the following code will run:

            if result == None:
                prune_count += 1
                import_board_data(game_board, last_board, piece, initial_pos)
                continue

            elif col == 'w' and result <= crit_val[other_col]:
                all_moves[(piece, pos_1)] = result
                import_board_data(game_board, last_board, piece, initial_pos)


            elif col == 'b' and result >= crit_val[other_col]:
                all_moves[(piece, pos_1)] = result
                import_board_data(game_board, last_board, piece, initial_pos)


            else:
                prune_count += 1
                if depth == layer:
                    import_board_data(game_board, last_board, piece, initial_pos)
                    continue
                else:
                    import_board_data(game_board, last_board, piece, initial_pos)
                    return None

    if depth != layer:  # This will happen if nothing was pruned
        try:
            if col == 'w':
                max_val = max(all_moves.values())
                best_val = max_val

            else:
                min_val = min(all_moves.values())
                best_val = min_val
        except:
            return None
        else:

            return best_val

    if depth == layer:

        if col == 'w':
            max_val = max(all_moves.values())
            print(f'final result is {max_val}')
            best_moves = []
            for move, val in all_moves.items():
                if val == max_val:
                    best_moves.append(move)
        elif col == 'b':
            min_val = min(all_moves.values())
            print(f'final result is {min_val}')
            best_moves = []
            for move, val in all_moves.items():
                if val == min_val:
                    best_moves.append(move)

        final_move = random.choice(best_moves)

        return final_move  # [pos_0, pos_1]


def play_comp():
    pygame.init()
    # board_setup = board_setup_test()
    board_setup = board_setup_normal()
    new_board = Board(board_setup)  # Setup default board
    new_board.populate_dicts()
    full_board_update(new_board)
    move_num = 0  # White will move on even numbers

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    screen.fill(pygame.Color('white'))

    load_images()  # Load chess piece images once

    running = True

    sq_selected = ()  # No square is selected intitially (row,col)
    player_clicks = []  # keep track of player clicks [(row_1, col_1), (row_2, col_2)]
    legal_moves = []  # Hold legal moves for selected player

    turn = {0: 'w', 1: 'b'}  # If move_num is even, it is white's turn. If move_num is odd, it is black's turn

    while running:
        for e in pygame.event.get():

            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                location = pygame.mouse.get_pos()  # x and y location of mouse
                col = location[0] // SQ_SIZE  # row of square clicked on
                row = location[1] // SQ_SIZE  # col of square clicked on

                if sq_selected == (row, col):  # Undo if click same square twice
                    sq_selected = ()
                    player_clicks = []
                    legal_moves = []
                else:
                    sq_selected = (row, col)
                    try:
                        print(new_board.get_piece(sq_selected))
                    except:
                        pass
                    player_clicks.append(sq_selected)  # Will append for either first or second click
                    if len(player_clicks) == 1:
                        if new_board.get_piece(sq_selected) == '--':  # Reset if first click is blank
                            sq_selected = ()
                            player_clicks = []
                            legal_moves = []
                        elif new_board.get_piece(sq_selected).colour != turn[
                            move_num % 2]:  # Reset if first click is wrong colour
                            sq_selected = ()
                            player_clicks = []
                            legal_moves = []
                        else:
                            try:
                                piece = new_board.get_piece(sq_selected)
                                legal_moves = team_legal_moves(new_board, 'w')[piece]
                            except:
                                sq_selected = ()
                                player_clicks = []
                                legal_moves = []

                if len(player_clicks) == 2:  # If two selected have been given

                    if sq_selected in legal_moves:
                        make_move(new_board, new_board.get_piece(player_clicks[0]), sq_selected)  # Make move
                        move_num += 2
                        sq_selected = ()
                        legal_moves = []
                        full_board_update(new_board)
                        print(f'Your move results in : {board_val(new_board)}')
                        new_board.draw_board(screen, legal_moves, sq_selected)
                        clock.tick(MAX_FPS)
                        pygame.display.update()
                        b_outcome = end_game(new_board, 'b')
                        if new_board.black_king in new_board.team_moves['w']:
                            print('Black king is in the firing line!')
                        if b_outcome[0] == True:
                            print('Check-mate')
                            print(new_board.check['b'])
                            end_screen(screen, "Check mate! White wins!")
                            running = False
                        elif b_outcome[1] == True:
                            print('Stale-mate')
                            print(new_board.check['b'])
                            end_screen(screen, "This game is a draw!")
                            running = False

                        else:
                            if len(new_board.piece_dicts) < 8 and (
                                    (new_board.check['w'] is True) or (new_board.check['b'] is True)):
                                depth = 4
                                print("Give me a moment, I am going to take my time with this one!")
                            elif len(new_board.piece_dicts) < 16 or (new_board.check['w'] is True) or (
                                    new_board.check['b'] is True):
                                depth = 3
                                print("Let me think...")
                            else:
                                depth = 2
                            print(f'Computer working at depth {depth}')
                            instructions = alpha_beta_algorithm(new_board, 'b', depth)

                            make_move(new_board, instructions[0], instructions[1])
                            full_board_update(new_board)
                            print(new_board)
                            print(f'My move results in : {board_val(new_board)}')
                            w_outcome = end_game(new_board, 'w')
                            if w_outcome[0]:
                                print('Check-mate')
                                print(new_board.check['w'])
                                end_screen(screen, "Check mate! Black wins!")
                                running = False
                            elif w_outcome[1]:
                                print('Stale-mate')
                                print(new_board.check['w'])
                                end_screen(screen, "This game is a draw!")
                                running = False
                            full_board_update(new_board)
                            new_board.draw_board(screen, legal_moves, sq_selected)
                            clock.tick(MAX_FPS)
                            pygame.display.update()
                        # running = False
                    sq_selected = ()  # Reset selections
                    player_clicks = []
                    legal_moves = []

        new_board.draw_board(screen, legal_moves, sq_selected)
        clock.tick(MAX_FPS)
        pygame.display.update()


def play_person():
    pygame.init()
    # board_setup = board_setup_test()
    board_setup = board_setup_normal()
    new_board = Board(board_setup)  # Setup default board
    new_board.populate_dicts()
    full_board_update(new_board)
    move_num = 0  # White will move on even numbers

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    screen.fill(pygame.Color('white'))

    load_images()  # Load chess piece images once

    running = True

    sq_selected = ()  # No square is selected intitially (row,col)
    player_clicks = []  # keep track of player clicks [(row_1, col_1), (row_2, col_2)]
    legal_moves = []  # Hold legal moves for selected player

    turn = {0: 'w', 1: 'b'}  # If move_num is even, it is white's turn. If move_num is odd, it is black's turn

    while running:
        for e in pygame.event.get():

            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                location = pygame.mouse.get_pos()  # x and y location of mouse
                col = location[0] // SQ_SIZE  # row of square clicked on
                row = location[1] // SQ_SIZE  # col of square clicked on

                if sq_selected == (row, col):  # Undo if click same square twice
                    sq_selected = ()
                    player_clicks = []
                    legal_moves = []
                else:
                    sq_selected = (row, col)
                    try:
                        print(new_board.get_piece(sq_selected))
                    except:
                        pass
                    player_clicks.append(sq_selected)  # Will append for either first or second click
                    if len(player_clicks) == 1:
                        if new_board.get_piece(sq_selected) == '--':  # Reset if first click is blank
                            sq_selected = ()
                            player_clicks = []
                            legal_moves = []
                        elif new_board.get_piece(sq_selected).colour != turn[
                            move_num % 2]:  # Reset if first click is wrong colour
                            sq_selected = ()
                            player_clicks = []
                            legal_moves = []
                        else:
                            try:
                                piece = new_board.get_piece(sq_selected)
                                legal_moves = team_legal_moves(new_board, turn[move_num % 2])[piece]
                            except:
                                sq_selected = ()
                                player_clicks = []
                                legal_moves = []

                if len(player_clicks) == 2:  # If two selected have been given

                    if sq_selected in legal_moves:
                        make_move(new_board, new_board.get_piece(player_clicks[0]), sq_selected)  # Make move
                        move_num += 1
                        sq_selected = ()
                        legal_moves = []
                        full_board_update(new_board)
                        print(f'Your move results in : {board_val(new_board)}')
                        new_board.draw_board(screen, legal_moves, sq_selected)
                        clock.tick(MAX_FPS)
                        pygame.display.update()
                        outcome = end_game(new_board, turn[(move_num + 1) % 2])
                        if outcome[0]:
                            print('Check mate!')
                            end_screen(screen, "Check mate!")
                            running = False
                        elif outcome[1]:
                            print('Stale-mate')
                            end_screen(screen, "This game is a draw!")
                            running = False

                            full_board_update(new_board)
                            new_board.draw_board(screen, legal_moves, sq_selected)
                            clock.tick(MAX_FPS)
                            pygame.display.update()
                        # running = False
                    sq_selected = ()  # Reset selections
                    player_clicks = []
                    legal_moves = []

        new_board.draw_board(screen, legal_moves, sq_selected)
        clock.tick(MAX_FPS)
        pygame.display.update()
    new_board.draw_board(screen, legal_moves, sq_selected)
    clock.tick(MAX_FPS)
    pygame.display.update()


play_comp()