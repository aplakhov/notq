import click
from notq.db import db_execute_commit
from notq.karma import get_best_users

@click.command('give-karma-based-gold')
@click.argument('period')
@click.option('-k', '--karma', type=int)
@click.option('-r', '--real', is_flag=True, default=False)
def give_gold_command(period, karma, real):
    '''
    Simplest method of giving gold. Give gold to every user with karma>=threshold in given time period. 
    If "--real" flag is not specified, it's a dry run, nothing is written into db.
    '''
    #select everyone with karma>x for the period
    users = get_best_users(period)
    for user in users:
        user_karma = user['karma']
        if not isinstance(user_karma, int): # can be 'epsilon'
            continue
        if user['is_golden']:
            continue
        if user_karma < karma:
            continue
        print("Giving gold to ", user['username'])
        if real:
            db_execute_commit('UPDATE notquser SET is_golden=:t WHERE username=:u', t=True, u=user['username'])
