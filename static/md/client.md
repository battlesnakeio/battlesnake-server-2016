# BattleSnake Client API

For more information visit [battlesnake.io](http://www.battlesnake.io).

<br>

## General Client Rules

* Game clients must exist at a valid HTTP URL capable of responding to the requests specified below.
* Clients must respond to all requests within 2 seconds or face disqualification.
* All requests must return a 200 status code and a valid response body or face disqualification.

<br>

## POST /start

Signals the start of a BattleSnake game. All clients must respond with a 200 status code and valid response object or risk being disqualified.

Since game IDs may be re-used, this endpoint may be called multiple times with the same game ID. Clients use this call to reset any saved game state for the given game ID.

<br>

##### Request

* **game_id** - ID of the game about to start
* **width** - The width of the game board (the x axis)
* **height** - The height of the game board (the y axis)s

```javascript
{
  "game_id": "hairy-cheese",
  "width": 20,
  "height": 20
}
```

<br>

##### Response

* **name** - friendly name of this snake
* **color** - display color for this snake (must be CSS compatible)
* **head_url** _(optional)_ - full URL for a 20x20 snake head image
* **taunt** _(optional)_ - string message for other snakes

```js
{
  "name": "Team Gregio",
  "color": "#ff0000",
  "head_url": "http://img.server.com/snake_head.png",
  "taunt": "Let's rock!"
}
```

<br>

## POST /move

Failing to respond appropriately
if invalid response, snake moves forward

<br>

##### Request

* **game_id** - ID of the game being played
* **turn** - turn number being played
* **board** - current board state (see [Board State Objects](#board-state-objects))
* **snakes** - array of snakes in play (see [Snake Objects](#snake-objects))
* **food** - array of food coordinates (see [Food Arrays](#food-arrays))

```javascript
{
  "game_id": "hairy-cheese",
  "turn": 1,
  "board": [
    [<BoardTile>, <BoardTile>, ...],
    [<BoardTile>, <BoardTile>, ...],
    ...
  ],
  "snakes":[<Snake>, <Snake>, ...],
  "food": [[1, 4], [3, 0], [5, 2]]
}
```

<br>

##### Response

* **move** - this snakes' next move, one of: ["up", "down", "left", "right"]
* **taunt** _(optional)_ - string message to other snakes

```javascript
{
  "move": "up",
  "taunt": "go snake yourself"
}
```

<br>

## POST /end

Indicates that a specific game has ended. No more move requests will be made. No response required.

<br>

##### Request

* **game_id** - id of game being ended

```javascript
{
  "game_id": "hairy-cheese"
}
```

<br>

##### Response

_Responses to this endpoint will be ignored._

<br>

## Board State Objects

Describes the state of the board for a specific game. Board State Objects are comprised of a 2-Dimensional array of Board Tiles. This array is indexed to match board coordinates, such that the board tile for coordinates (1, 5) are accessible at _board[1][5]_. Board coordinates are 0-based with [0][0] representing the top left corner.

![board.jpg](/static/img/board.jpg)

<br>

##### Example Board State

```javascript
[
  [<BoardTile>, <BoardTile>, ...],
  [<BoardTile>, <BoardTile>, ...],
  ...
]
```

<br>

##### Board Tiles

* **state** - one of ["head", "body", "food", "empty"]
  * _head_ - occupied by snake head (see snake attribute)
  * _body_ - occupied by snake body (see snake attribute)
  * _food_ - contains an uneaten piece of food
  * _empty_ - an empty tile
* **snake** _(optional)_ - name of occupying snake (if applicable)

```javascript
{
  "state": "head",
  "snake": "Noodlez"
}
```

<br>

## Snake Objects

Describes the state of a single snake in a particular game.

##### Attributes

* **name** - friendly name of this snake (must be unique)
* **coords** - ordered array of coordinates indicating location of this snake on the board (from head to tail)
* **score** - current score
* **color** - display color for this snake
* **head_url** - full URL to 20x20 snake head image
* **taunt** - latest string message to other snakes
* **last_eaten** - last turn this snake has grown, use this to determine life/hunger level (This field only exists if the snake has grown this game.  If this field is not present, treat it as 0)

```javascript
{
  "name": "Noodlez",
  "coords": [[0, 0], [0, 1], [0, 2], [1, 2]],
  "score": 4,
  "color": "#ff0000",
  "head_url": "http://img.server.com/snake_head.png",
  "taunt": "I'm one slippery noodle",
  "last_eaten": 3
}
```

## Food Arrays

An array of coordinate tuples representing food locations.

##### Example

```javascript
[
  [1, 4], [3, 0], [5, 2]
]
```
