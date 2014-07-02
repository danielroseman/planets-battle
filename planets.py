import os
import random

from google.appengine.api import users
from google.appengine.ext import ndb
import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
        loader=jinja2.FileSystemLoader(
            os.path.dirname(__file__)),
        extensions=['jinja2.ext.autoescape'],
        autoescape=True)

class Home(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        #player = Player.query(Player.user=user)
        while True:
            planet_number = random.randint(1, 100)
            key = ndb.Key('Planet', str(planet_number))
            planet = key.get()
            if planet is None:
                planet = Planet(
                    key=key,
                    position=planet_number,
                    owner=user)
                planet.put()
                break
        if planet is None:
            msg = "Sorry, no planets available"
        else:
            msg = 'Your planet is %s' % planet_number
        self.response.write('<p>%s</p>' % msg)

class GameScreen(webapp2.RequestHandler):
    def get_context(self):
        self.user = users.get_current_user()
        planets = Planet.query(Planet.owner==self.user)
        return {'user': self.user, 'planets': planets}

    def get(self):
        context = self.get_context()
        template = JINJA_ENVIRONMENT.get_template('game.html')
        self.response.write(template.render(context))

    def post(self):
        context = self.get_context()
        planet_number = self.request.get('planet_number')
        if planet_number:
            msg = self.upgrade_planet(planet_number)
        attack_number = self.request.get('attack')
        if attack_number:
            msg, attacked = self.attack_planet(attack_number)
            context['attacked'] = attacked

        context['msg'] = msg
        template = JINJA_ENVIRONMENT.get_template('game.html')
        self.response.write(template.render(context))

    def upgrade_planet(self, planet_number):
        key = ndb.Key('Planet', planet_number)
        planet = key.get()
        if planet.level < 3:
            planet.level += 1
            planet.population += 100
            planet.put()
            msg = 'Planet %s was upgraded' % planet_number
        else:
            msg = 'Planet %s could not be upgraded' % planet_number
        return msg

    def attack_planet(self, attack_number):
        attacker_key = ndb.Key(Planet, self.request.get('attack_with'))
        attacker = attacker_key.get()

        attacked_key = ndb.Key('Planet', attack_number)
        attacked_planet = attacked_key.get()

        if attacked_planet is None:
            attacked_planet = Planet(
                    key=attacked_key,
                    owner=self.user,
                    position=int(attack_number))
            attacked_planet.put()
            result = 'Attack succesful'
        elif attacker.population > attacked_planet.population:
            attacked_planet.owner = self.user
            attacked_planet.put()
            result = 'Attack successful'
        else:
            attacker.population = 0
            attacker.put()
            result = 'attack unsuccessful'
        return result, attacked_planet


class Planet(ndb.Model):
    name = ndb.StringProperty()
    position = ndb.IntegerProperty()
    owner = ndb.UserProperty()
    level = ndb.IntegerProperty(default=1)
    population = ndb.IntegerProperty(default=100)


application = webapp2.WSGIApplication([
    ('/', Home),
    ('/game', GameScreen),
], debug=True)
