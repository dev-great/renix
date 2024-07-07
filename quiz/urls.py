# renix/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('checkAnswer/<uid>/<str:createObj>',
         views.check_answer, name='check_answer'),
    path('quizzes/quizzes/quiz/', views.quiz, name='quiz'),
    #     path('signUp/', views.sign_up, name='sign_up'),
    path('signIn/', views.sign_in, name='sign_in'),
    path('signOut/', views.logout_view, name='sign_out'),
    path('loadAttendedQuestionData/<uid>', views.loadAttendedQuestionData,
         name='load_attended_question_data'),
    path('myprofile/', views.myprofile, name='myprofile'),
    path('quiz_attempts/', views.quizAttempts, name='quiz_attempts'),
    path('quizzes/', views.quizzes, name='quizzes'),
    path('subscription/', views.subscription, name='subscription'),
    path('settings/', views.settings, name='settings'),
    path('enrolled_courses/', views.enrolled_courses, name='enrolled_courses'),
    path('success_screen/', views.success_screen, name='success_screen'),
    path('quiz/<uuid:quiz_id>/questions/',
         views.quiz_questions, name='quiz_questions'),
    path('course/', views.study_detail, name='study_detail'),
    path('topics/', views.study_topics, name='study_topics'),
    path('quiz_detail/', views.start_quiz, name='quiz_detail'),
    path('help/', views.help, name='help'),
    path('create-question/', views.create_question, name='create_question'),
    path('text_analitics', views.text_analitics, name='text_analitics')
]
