# -*- test-case-name: imaginary.test.test_concept -*-

"""

Textual formatting for game objects.

"""
import types

from zope.interface import implements

from twisted.python.components import registerAdapter

from imaginary import iimaginary, iterutils, text as T


class Gender(object):
    """
    enum!
    """
    MALE = 1
    FEMALE = 2
    NEUTER = 3



class Noun(object):
    """
    This is a language wrapper around a Thing.

    It is separated into its own class for two reasons:

     - You should try to keep your game-logic self-contained and avoid
       polluting it with lots of constant strings, so that porting to new
       interfaces (text prototype -> isometric final implementation) is easy.
       It's easier to read the code that way and make changes to the logic even
       if you don't want to move to a different interface.


     - It would be nice if text games could be internationalized by separating
       the formatting logic from the game logic.  In an extreme case, it would
       be SUPER-COOL if people could be playing the same game in french and
       english on the same server, simply by changing a setting on their
       client.
    """


    def __init__(self, thing):
        self.thing = thing
        self.unique = False


    def shortName(self):
        return ExpressString(self.thing.name)


    def nounPhrase(self):
        if self.thing.proper:
            return self.shortName()
        return ExpressList([self.indefiniteArticle(), self.shortName()])


    def definiteNounPhrase(self):
        if self.thing.proper:
            return self.shortName()
        return ExpressList([self.definiteArticle(), self.shortName()])


    def indefiniteArticle(self):
        # XXX TODO FIXME: YTTRIUM
        if self.thing.name[0].lower() in u'aeiou':
            return u'an '
        return u'a '


    def definiteArticle(self):
        return u'the '


    def heShe(self):
        """
        Return the personal pronoun for the wrapped thing.
        """
        x = {Gender.MALE: u'he',
             Gender.FEMALE: u'she'
             }.get(self.thing.gender, u'it')
        return ExpressString(x)


    def himHer(self):
        """
        Return the objective pronoun for the wrapped thing.
        """
        x = {Gender.MALE: u'him',
             Gender.FEMALE: u'her'
             }.get(self.thing.gender, u'it')
        return ExpressString(x)


    def hisHer(self):
        """
        Return a possessive pronoun that cannot be used after 'is'.
        """
        x = {Gender.MALE: u'his',
             Gender.FEMALE: u'her' # <-- OMG! hers!
             }.get(self.thing.gender, u'its')
        return ExpressString(x)


    #FIXME: add his/hers LATER

    def description(self):
        return DescriptionConcept(self.thing)



class BaseExpress(object):
    implements(iimaginary.IConcept)

    def __init__(self, original):
        self.original = original

    def plaintext(self, observer):
        return T.flatten(self.vt102(observer), useColors=False)



class DescriptionConcept(BaseExpress):
    implements(iimaginary.IConcept)

    def __init__(self, thing):
        self.thing = thing
        self.noun = Noun(thing)


    def vt102(self, observer):
        exitNames = list(self.thing.getExitNames())
        if exitNames:
            exits = [T.bold, T.fg.green, u'( ', [T.fg.normal, T.fg.yellow, iterutils.interlace(u' ', exitNames)], u' )', u'\n']
        else:
            exits = u''

        description = u''
        if self.thing.description:
            description = (T.fg.green, self.thing.description, u'\n')

        descriptionComponents = []
        for pup in self.thing.powerupsFor(iimaginary.IDescriptionContributor):
            descriptionComponents.append(pup.conceptualize().vt102(observer))

        return [
            [T.bold, T.fg.green, u'[ ', [T.fg.normal, self.thing.name], u' ]\n'],
            exits,
            description,
            descriptionComponents]



class ExpressNumber(BaseExpress):
    implements(iimaginary.IConcept)

    def vt102(self, observer):
        return str(self.original)



class ExpressString(BaseExpress):
    implements(iimaginary.IConcept)

    def __init__(self, original, capitalized=False):
        self.original = original
        self._cap = capitalized


    def vt102(self, observer):
        if self._cap:
            return self.original[:1].upper() + self.original[1:]
        return self.original


    def capitalizeConcept(self):
        return ExpressString(self.original, True)



class ExpressList(BaseExpress):
    implements(iimaginary.IConcept)

    def concepts(self, observer):
        return map(iimaginary.IConcept, self.original)

    def vt102(self, observer):
        return [x.vt102(observer) for x in self.concepts(observer)]

    def capitalizeConcept(self):
        return Sentence(self.original)




class Sentence(ExpressList):
    def vt102(self, observer):
        o = self.concepts(observer)
        if o:
            o[0] = o[0].capitalizeConcept()
        return [x.vt102(observer) for x in o]


    def capitalizeConcept(self):
        return self



registerAdapter(ExpressNumber, int, iimaginary.IConcept)
registerAdapter(ExpressNumber, long, iimaginary.IConcept)
registerAdapter(ExpressString, str, iimaginary.IConcept)
registerAdapter(ExpressString, unicode, iimaginary.IConcept)
registerAdapter(ExpressList, list, iimaginary.IConcept)
registerAdapter(ExpressList, tuple, iimaginary.IConcept)
registerAdapter(ExpressList, types.GeneratorType, iimaginary.IConcept)


class ItemizedList(BaseExpress):
    implements(iimaginary.IConcept)

    def __init__(self, listOfConcepts):
        self.listOfConcepts = listOfConcepts


    def concepts(self, observer):
        return self.listOfConcepts


    def vt102(self, observer):
        return ExpressList(
            itemizedStringList(self.concepts(observer))).vt102(observer)


    def capitalizeConcept(self):
        listOfConcepts = self.listOfConcepts[:]
        if listOfConcepts:
            listOfConcepts[0] = iimaginary.IConcept(listOfConcepts[0]).capitalizeConcept()
        return ItemizedList(listOfConcepts)



def itemizedStringList(desc):
    if len(desc) == 1:
        yield desc[0]
    elif len(desc) == 2:
        yield desc[0]
        yield u' and '
        yield desc[1]
    elif len(desc) > 2:
        for ele in desc[:-1]:
            yield ele
            yield u', '
        yield u'and '
        yield desc[-1]

