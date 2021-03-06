import React, { Component } from 'react';
import RouterContext from 'react-router';

const GAME_MODES = [
  'classic',
  'advanced'
];

export default class GameCreate extends Component {
  state = {
    availableTeams: [],
    addedTeams: [],
    selectedTeam: null,
    currentWidth: 17,
    currentHeight: 17,
    currentTimeout: 1,
    isLoading: false,
    mode: 'classic'
  };

  _persistState () {
    localStorage['game_state'] = JSON.stringify(this.state);
  };

  _restoreState () {
    let oldState = {}
    let { state } = this.props.location

    try {
      oldState = JSON.parse(localStorage['game_state']);
    } catch (e) {
      // No state saved yet. Default it
    }

    // If were coming from a rematch
    if (state) {
      oldState.addedTeams = state.rematchTeams
    }

    this.setState($.extend(this.state, oldState));
  };

  handleGameCreate = (e) => {
    e.preventDefault();

    let gameData = {
      teams: this.state.addedTeams,
      width: parseInt(this.state.currentWidth),
      height: parseInt(this.state.currentHeight),
      turn_time: parseFloat(this.state.currentTimeout),
      mode: this.state.mode
    };

    this.setState({isLoading: true});

    $.ajax({
        type: 'POST',
        url: '/api/games',
        data: JSON.stringify(gameData)
      })
      .done((response) => {
        if (response.data.error) {
          alert(response.data.message);
          this.setState({isLoading: false});
        } else {
          this.setState({isLoading: false});
          this.props.history.push('/app/games/' + response.data.game._id);
        }
        this._persistState();
      })
      .error((xhr, textStatus, errorThrown) => {
        alert(xhr.responseJSON.message);
        this.setState({isLoading: false});
      });
  };

  handleWidthChange = (e) => {
    this.setState({currentWidth: e.target.value});
  };

  handleHeightChange = (e) => {
    this.setState({currentHeight: e.target.value});
  };

  handleTeamChange = (e) => {
    let id = e.target.value;
    let team = this.state.availableTeams.find((team) => { return team._id == id; });
    this.setState({selectedTeam: team});
  };

  handleDeleteTeam = (i, e) => {
    let addedTeams = this.state.addedTeams;

    let team = addedTeams[i];
    addedTeams.splice(i, 1);

    this.setState({
      addedTeams: addedTeams
    });
  };

  handleAddTeam = (e) => {
    e.preventDefault();
    let currentTeam = this.state.selectedTeam;
    let addedTeams = this.state.addedTeams;

    addedTeams.push(currentTeam);

    this.setState({
      selectedTeam: null,
      addedTeams: addedTeams
    });
  };

  handleModeSelect = (e) => {
    this.setState({mode: e.target.value})
  };

  componentDidMount () {
    this._restoreState();

    // fetch list of teams
    $.ajax({
      type: 'GET',
      url: '/api/teams/'
    })
    .done((response) => {
      this.setState({availableTeams: response.data});
    });
  }

  render () {
    let offset = 0;
    let buildOption = (value, disabled, name) => {
      offset++;
      return (
        <option key={'team_opt_' + offset} value={value} disabled={disabled}>
          {name}
        </option>
      );
    };

    let buildTeamOption = (team) => {
      let teamname = team.teamname;
      teamname = `${teamname} [${team.game_mode}]`

      let disabled = false;
      for (let j = 0; j < this.state.addedTeams.length; j++) {
        let t = this.state.addedTeams[j];
        let isAddedAlready = t._id === team._id;
        if (isAddedAlready) {
          disabled = true;
          teamname = `${teamname} - Added`;
          break;
        }
      }
      return buildOption(team._id, disabled, teamname);
    };

    let buildTeamOptionList = (teamlist) => {
      return teamlist.map((team, i) => {
        return buildTeamOption(team);
      })
    }

    // Bucketed and ordered
    let teamOpts = [buildOption('divider', 'true', 'Select a team')];

    let bountySnakes = this.state.availableTeams.filter((team) => { return team.type === 'bounty'; });
    if (bountySnakes.length > 0) {
      teamOpts = teamOpts.concat(buildOption('divider', 'true', '–––– Bounty snakes ––––'));
      teamOpts = teamOpts.concat(buildTeamOptionList(bountySnakes));
    }

    let testSnakes = this.state.availableTeams.filter((team) => { return team.type === 'test'; });
    if (testSnakes.length > 0) {
      teamOpts = teamOpts.concat(buildOption('divider', 'true', '–––– Test snakes ––––'));
      teamOpts = teamOpts.concat(buildTeamOptionList(testSnakes));
    }


    if (bountySnakes.length > 0 || testSnakes.length > 0) {
      teamOpts = teamOpts.concat(buildOption('divider', 'true', '–––– Competitor snakes ––––'));
    }
    let normalSnakes = this.state.availableTeams.filter((team) => { return team.type === 'normal'; });
    teamOpts = teamOpts.concat(buildTeamOptionList(normalSnakes));



    let gameModes = GAME_MODES.map((mode) => {
      return (
        <option key={mode} value={mode}>
          {mode}
        </option>
      )
    })

    let teamNames = this.state.addedTeams.map((team, i) => {
      return (
        <li key={'team_' + i}>
          <a href="#"
             className="pull-right"
             onClick={this.handleDeleteTeam.bind(null, i)}>
            &times;
          </a>
          <p>{team.teamname} {['bounty', 'test'].includes(team.type) ? team.type : ''}[{team.game_mode}]</p>
        </li>
      );
    });

    if (this.state.addedTeams.length === 0) {
      teamNames.push(
        <li key="team_no_team_selected">
          <p>You have no teams added. Select a team in the box below...</p>
        </li>
      );
    }

    return (
      <div className="container">
        <form>
          <div className="row">
            <div className="col-md-12">
              <h2>Create Game</h2>
              <br />
            </div>
          </div>
          <div className="row">
            <div className="col-md-5">
              <h3>Teams Entering The Game:</h3>
              <ul className="team-member-list list-unstyled">
                {teamNames}
              </ul>
            </div>
            <div className="col-md-5 col-md-push-2">
              <div className="form-group">
                <label>Add a team</label>
                <div className="input-group ">
                  <select name="teamname"
                          className="form-control"
                          onChange={this.handleTeamChange}>
                    {teamOpts}
                  </select>
                  <span className="input-group-btn">
                    <button type="submit"
                            className="btn btn-success"
                            disabled={this.state.selectedTeam ? false : 'disabled'}
                            onClick={this.handleAddTeam}>
                      Add Team
                    </button>
                  </span>
                </div>
              </div>
              <div className="form-group">
                <label>Width</label>
                <input type="number"
                       className="form-control"
                       placeholder="width"
                       min="5"
                       max="50"
                       value={this.state.currentWidth}
                       onChange={this.handleWidthChange}
                       disabled={this.state.isLoading}
                />
              </div>
              <div className="form-group">
                <label>Height</label>
                <input type="number"
                       className="form-control"
                       placeholder="height"
                       min="5"
                       max="50"
                       value={this.state.currentHeight}
                       onChange={this.handleHeightChange}
                       disabled={this.state.isLoading}
                />
              </div>
              <div className="form-group">
                <label>Game Mode</label>
                <select name="mode"
                        className="form-control"
                        value={this.state.mode}
                        disabled={this.state.isLoading}
                        onChange={this.handleModeSelect}>
                  {gameModes}
                </select>
              </div>
            </div>
          </div>
          <div className="row">
            <div className="col-md-12">
              <br />
              <button type="button"
                      className="btn btn-lg btn-block btn-success"
                      onClick={this.handleGameCreate}
                      disabled={this.state.isLoading}>
                {this.state.isLoading ? 'Contacting snakes...' : 'Start Game'}
              </button>
            </div>
          </div>
        </form>
      </div>
    );
  }

}
