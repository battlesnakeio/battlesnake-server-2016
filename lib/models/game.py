import logging

from lib.models.base import Model
from lib.redis_client import Queue
from lib.words import get_noun, get_adjective


logger = logging.getLogger(__name__)


class Game(Model):
    STATE_CREATED = 'created'
    STATE_PAUSED = 'paused'
    STATE_MANUAL = 'manual'
    STATE_READY = 'ready'
    STATE_PLAYING = 'playing'
    STATE_DONE = 'done'

    MODE_CLASSIC = 'classic'
    MODE_ADVANCED = 'advanced'
    MODE_VALUES = [MODE_CLASSIC, MODE_ADVANCED]

    ready_queue_regular = Queue('games:ready.regular')
    ready_queue_admin = Queue('games:ready.admin')

    queues = {
        'regular': ready_queue_regular,
        'admin': ready_queue_admin
    }

    def __init__(
            self,
            id=None,
            width=10,
            height=10,
            state=STATE_CREATED,
            stats=None,
            turn_time=1.0,
            is_live=True,
            team_id=None,
            team_ids=[],
            mode=MODE_CLASSIC):

        super(Game, self).__init__()

        self.id = id or Game._generate_id()
        self.state = state
        self.stats = stats or {}
        self.width = width
        self.height = height
        self.turn_time = turn_time
        self.is_live = is_live
        self.team_id = team_id
        self.team_ids = team_ids
        self.mode = mode

    def to_dict(self):
        return {
            '_id': self.id,
            'state': self.state,
            'stats': self.stats,
            'width': self.width,
            'height': self.height,
            'turn_time': self.turn_time,
            'is_live': self.is_live,
            'team_id': self.team_id,
            'team_ids': self.team_ids,
            'mode': self.mode
        }

    def mark_ready(self):
        """
        Mark game as ready for a worker to process
        """

        self.state = Game.STATE_READY
        self.save()

        from lib.models.team import Team
        team = Team.find_one({'_id': self.team_id})

        if not team or team.type != Team.TYPE_ADMIN:
            self.ready_queue_regular.enqueue(self.id)
        else:
            self.ready_queue_admin.enqueue(self.id)

    @staticmethod
    def _generate_id():
        return '%s-%s' % (get_adjective(), get_noun())

    @classmethod
    def from_dict(cls, obj):
        instance = cls(
            id=obj['_id'],
            state=obj['state'],
            width=obj['width'],
            stats=obj['stats'],
            height=obj['height'],
            turn_time=obj['turn_time'],
            is_live=obj.get('is_live', False),
            team_id=obj.get('team_id', None),
            team_ids=obj.get('team_ids', []),
            mode=obj.get('mode', cls.MODE_CLASSIC)
        )

        instance._add_timestamps(obj)
        return instance


class GameState(Model):
    TILE_STATE_EMPTY = 'empty'
    TILE_STATE_FOOD = 'food'
    TILE_STATE_SNAKE_HEAD = 'head'
    TILE_STATE_SNAKE_BODY = 'body'
    TILE_STATE_GOLD = 'gold'
    TILE_STATE_WALL = 'wall'

    TILE_STATES = [
        TILE_STATE_EMPTY,
        TILE_STATE_SNAKE_HEAD,
        TILE_STATE_SNAKE_BODY,
        TILE_STATE_FOOD,
        TILE_STATE_GOLD,
        TILE_STATE_WALL
    ]

    def __init__(self, game_id, width, height, mode=Game.MODE_CLASSIC):

        super(GameState, self).__init__()

        self.id = None
        self.game_id = game_id
        self.width = width
        self.height = height
        self.turn = 0
        self.is_done = False
        self.snakes = []
        self.dead_snakes = []
        self.food = []
        self.gold = []
        self.walls = []
        self.mode = mode

    def insert(self):
        if not self.id:
            self.id = '%s-%s' % (self.game_id, self.turn)
        return super(GameState, self).insert()

    def generate_board(self):
        board = []
        for x in range(self.width):
            row = []
            for y in range(self.height):
                row.append({'state': GameState.TILE_STATE_EMPTY})
            board.append(row)

        for snake in self.snakes:
            for i, coord in enumerate(snake.coords):
                if i == 0:
                    board[coord[0]][coord[1]]['state'] = GameState.TILE_STATE_SNAKE_HEAD
                else:
                    board[coord[0]][coord[1]]['state'] = GameState.TILE_STATE_SNAKE_BODY
                board[coord[0]][coord[1]]['snake'] = snake.name

        for coord in self.food:
            board[coord[0]][coord[1]]['state'] = GameState.TILE_STATE_FOOD

        for coord in self.gold:
            board[coord[0]][coord[1]]['state'] = GameState.TILE_STATE_GOLD

        for coord in self.walls:
            board[coord[0]][coord[1]]['state'] = GameState.TILE_STATE_WALL

        return board

    def sanity_check(self):
        if not isinstance(self.game_id, basestring):
            raise ValueError('Sanity Check Failed: game_id not int, %s' % self.game_id)
        if not isinstance(self.turn, int):
            raise ValueError('Sanity Check Failed: turn is not int, %s' % self.turn)

        for snake in self.snakes:
            for coord in snake.coords:
                for check_snake in self.snakes:
                    if snake.team_id == check_snake.team_id:
                        continue
                    if coord in check_snake.coords:
                        raise ValueError('board.snakes contains overlapping coords.')
                if coord in self.food:
                    raise ValueError('board.snakes and board.food contain overlapping coords.')
                if coord[0] > (self.width - 1):
                    raise ValueError('board.snakes outside bounds of self.board')
                if coord[0] < 0:
                    raise ValueError('board.snakes outside bounds of self.board')
                if coord[1] > (self.height - 1):
                    raise ValueError('board.snakes outside bounds of self.board')
                if coord[1] < 0:
                    raise ValueError('board.snakes outside bounds of self.board')

    def to_dict(self, include_board=False):
        d = {
            '_id': self.id,
            'game_id': self.game_id,
            'is_done': self.is_done,
            'turn': self.turn,
            'snakes': [snake.to_dict() for snake in self.snakes],
            'dead_snakes': [snake.to_dict() for snake in self.dead_snakes],
            'food': self.food[:],
            'gold': self.gold[:],
            'walls': self.walls[:],
            'width': self.width,
            'height': self.height,
            'mode': self.mode,
        }

        if include_board:
            d['board'] = self.generate_board()

        return d

    @classmethod
    def from_dict(cls, obj):
        game_state = cls(obj['game_id'], obj['width'], obj['height'], obj['mode'])
        game_state.id = obj['_id']
        game_state.turn = obj['turn']
        game_state.is_done = obj['is_done']
        game_state.food = obj['food']
        game_state.gold = obj['gold']
        game_state.walls = obj['walls']

        from lib.game.engine import Snake
        game_state.snakes = [Snake.from_dict(snake) for snake in obj['snakes']]
        game_state.dead_snakes = [Snake.from_dict(snake) for snake in obj['dead_snakes']]

        game_state.sanity_check()

        return game_state

    # Board State Pretty Printer
    def to_string(self):
        self.sanity_check()

        tile_map = {
            GameState.TILE_STATE_EMPTY: '_',
            GameState.TILE_STATE_FOOD: '*',
            GameState.TILE_STATE_GOLD: 'G',
            GameState.TILE_STATE_WALL: 'W',
            GameState.TILE_STATE_SNAKE_BODY: 'B',
            GameState.TILE_STATE_SNAKE_HEAD: 'H'
        }

        output = ''
        board = self.generate_board()

        for y in range(len(board[0])):
            for x in range(len(board)):
                output += tile_map[board[x][y]['state']]
            output += '\n'
        output += '\n'

        return output
