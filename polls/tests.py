import datetime

from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.urls import reverse

from .models import Question
from .views import ResultsView


class QuestionModelTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)


def create_question(question_text, days):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


def create_choices(question, choice_text):
    """
    Create a choice with the given `choice_text` and assign it to the given question.
    """
    return question.choice_set.create(choice_text=choice_text)


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question(self):
        """
        Questions with a pub_date in the past are displayed on the
        index page.
        """
        question = create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question],
        )

    def test_future_question(self):
        """
        Questions with a pub_date in the future aren't displayed on
        the index page.
        """
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        are displayed.
        """
        question = create_question(question_text="Past question.", days=-30)
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question],
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        question1 = create_question(question_text="Past question 1.", days=-30)
        question2 = create_question(question_text="Past question 2.", days=-5)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question2, question1],
        )


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5)
        url = reverse('polls:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_no_view_for_inexistent_question(self):  # m
        """
        The detail view of a question which does not exist should not be found
        """
        url = reverse('polls:detail', args=(2,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text.
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)

    def test_right_question(self):  # m
        """
        The detail view gets the right question
        """
        past_question = create_question(question_text='Is the right question?.', days=-5)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.id)


def setup_view(view, request, *args, **kwargs):
    """
    Mimic ``as_view()``, but returns view instance.
    Use this function to get view instances on which you can run unit tests,
    by testing specific methods.
    """

    view.request = request
    view.args = args
    view.kwargs = kwargs
    return view


class QuestionResultViewTests(TestCase):

    def test_no_result_view_for_inexistent_question(self):  # m
        """
        The detail view of a question which does not exist should not be found
        """
        url = reverse('polls:results', args=(2,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_error_on_vote_invalid_choices(self):  # m
        """
        The vote method of result view should return an error_message : 'You did not select a choice.' when there is no choice selected
        """
        factory = RequestFactory()
        past_question = create_question(question_text='Is the right question?.', days=-5)
        request = factory.post(f'/polls/{past_question.id}/vote/')
        url = reverse('polls:vote', args=(past_question.id,))
        response = self.client.post(url)
        self.assertContains(response, "You did not select a choice.")

    def test_voting_for_a_choice(self):  # m
        """
        The vote method of result view should return an error_message : 'You did not select a choice.' when there is no choice selected
        """
        factory = RequestFactory()
        past_question = create_question(question_text='Is the right question?.', days=-5)
        choice = create_choices(past_question, choice_text='Yes')
        request = factory.post(f'/polls/{past_question.id}/vote/')
        url = reverse('polls:vote', args=(past_question.id,))
        response = self.client.post(url, {'choice': choice.id})
        self.assertRedirects(response, f'/polls/{past_question.id}/results/')
