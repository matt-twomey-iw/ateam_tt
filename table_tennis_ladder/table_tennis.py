import click
import os

# import libraries in lib directory

from group import Group
from ladder import Ladder
from player import Player
import validation
from flask import Flask, request, render_template, redirect, url_for, abort, flash
from htmlify import Htmlify

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "static"
app.secret_key = b'im_batman'

welcome = r"""
          ,;;;!!!!!;;.
        :!!!!!!!!!!!!!!;    Infinity Works Graduate Scheme 2018
      :!!!!!!!!!!!!!!!!!;       Ash & Matt's Ping Pong Ladder Extravaganza
     ;!!!!!!!!!!!!!!!!!!!;          All Rights Reserved (c) 2018
    ;!!!!!!!!!!!!!!!!!!!!!
    ;!!!!!!!!!!!!!!!!!!!!'
    ;!!!!!!!!!!!!!!!!!!!'       o      .  _______ _______
     :!!!!!!!!!!!!!!!!'         \_ 0     /______//______/|   @_o
      ,!!!!!!!!!!!!!''            /\_,  /______//______/     /\
   ,;!!!''''''''''               | \    |      ||      |     / |
 .!!!!'
!!!!
"""

champ = r"""
  ___________
 '._==_==_=_.'
 .-\:      /-.
| (|:.     |) |
 '-|:.     |-'     Current Champ: %s !!!
   \::.    /
    '::. .'          %s is overwhelmed with a feeling of pride and accomplishment.
      ) (            %s has truly earned the adoration of his/her peers.
    _.' '._
   `-------`
"""


@app.errorhandler(404)
def page_not_found(e):
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'Ben0.png')
    return render_template('404.html')

@app.route("/")
def get_html():
    leaderboard_names = get_leaderboard_names()
    home_html = render_template("home.html", leaderboard_names=leaderboard_names)
    return home_html


@app.route("/", methods=["POST"])
def post_leaderboard():
    if request.method == "POST":
        leaderboard_name = request.form["leaderboard_name"]
        if not leaderboard_name.isalnum():
            flash("Invalid input - leaderboard name contains non-alphanumeric characters", "error")
            return get_html()
        else:
            create_group(leaderboard_name)
            return redirect(url_for("get_leaderboard_html", leaderboard=leaderboard_name))


@app.route("/<leaderboard>")
def get_leaderboard_html(leaderboard):
    
    lower_leaderboard = leaderboard.lower()
    print lower_leaderboard
    print get_leaderboard_names()
    if lower_leaderboard not in get_leaderboard_names():
        abort(404)
    
    cur_group = get_group(leaderboard)
    ladder = cur_group.get_ladder().get_rankings()
    
    html = Htmlify(leaderboard, ladder).gen_html()
    return html


@app.route("/<leaderboard>", methods=["POST"])
def record_match(leaderboard):
    if request.method == "POST":
        if "record_match_submit" in request.form:
            winner_name = request.form["winner_name"]
            loser_name = request.form["loser_name"]

            cur_group = get_group(leaderboard)
            ladder = cur_group.get_ladder()
            input_game(ladder, winner_name, loser_name)
        elif "add_player_submit" in request.form:
            player_name = request.form["playername"]

            cur_group = get_group(leaderboard)
            group_ladder = cur_group.get_ladder()
            group_ladder.add_player(player_name)
        elif "remove_player_submit" in request.form:
            player_name = request.form["playername"]

            cur_group = get_group(leaderboard)
            group_ladder = cur_group.get_ladder()
            group_ladder.remove_player(player_name)

        return get_leaderboard_html(leaderboard)


@app.route("/<leaderboard>", methods=["DELETE"])
def remove_player(leaderboard):
    if request.method == "DELETE":
        player_name = request.form["playername"]

        cur_group = get_group(leaderboard)
        group_ladder = cur_group.get_ladder()
        group_ladder.remove_player(player_name)

        return get_leaderboard_html(leaderboard)

def get_leaderboard_names():
    leaderboard_names = []
    for filename in os.listdir("group_ladders"):
        if not "." in filename and filename != "leaderboard_names":
            leaderboard_names.append(filename)
 
    return leaderboard_names


@click.command()
@click.argument('group')
@click.option('--new', '-n', is_flag=True, help='Flag to create new group ladders.')
@click.option('--add', '-a', multiple=True, help='Add player(s) to the ladder (multiple players require multiple --add flags).')
@click.option('--update', '-u', nargs=2, help='Update ladder with results of a game e.g. --update WINNER LOSER.')
@click.option('--view', '-v', is_flag=True, help='View the current ladder positions.')
@click.option('--remove', '-r', multiple=True, help='Remove player(s) from the ladder (multiple players require multiple --remove flags).')
@click.option('--champion', '-c', is_flag=True, help="Show the current champion and their pending title trophy.")
def main(group,
         new, add, update, view, remove, champion):
    """A simple program to view and administrate the IW Table Tennis ladder.

        Provide a GROUP name and use the options listed below to interact with the system."""

    print welcome

    if new and not update:
        create_group(group)
        return

    # read group namme argument from command line and get group
    cur_group = get_group(group)
    if not cur_group:
        return

    group_ladder = cur_group.get_ladder()
    print_ladder = True

    if add and validation.data_validation(add):
        for name in add:
            group_ladder.add_player(name)
    if remove:
        for name in remove:
            group_ladder.remove_player(name)
    if champion:
        name = group_ladder.get_champion().name
        print champ % (name, name, name)
        print_ladder = False
    if update and (validation.data_validation(update[0]) and validation.data_validation(update[1])):
        winner_name = update[0]
        loser_name = update[1]
        input_game(group_ladder, winner_name, loser_name)

    if print_ladder or view:
        print group_ladder


def input_game(ladder, winner_name, loser_name):
    winner = ladder.get_player(winner_name)
    loser = ladder.get_player(loser_name)
    if not winner:
        winner = Player(winner_name)
    if not loser:
        loser = Player(loser_name)
    ladder.update(winner, loser)


def create_group(name):
    new_group = Group(name)
    new_group.ladder.save()
    print "Successfully added new group ladder: '%s'." % name


def get_group(name):
    try:
        return Group(name)
    except:
        print "ERROR: Group with name '%s' does not exist! Check spelling and try again." % name
        return None


if __name__ == '__main__':
    main()
