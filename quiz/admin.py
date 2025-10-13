from django.contrib import admin
from .models import (
    Category, StudyCategoryModel, StudyTopicModel, StudyModel,
    Question, Answer, GivenQuizQuestions, Quiz, UserSubscription, UserProfile
)


# ---------- INLINE MODELS ----------
class AnswerInline(admin.StackedInline):
    model = Answer
    extra = 1
    show_change_link = True


class GivenQuizQuestionsInline(admin.TabularInline):
    model = GivenQuizQuestions
    extra = 0
    readonly_fields = ('question', 'answer', 'points', 'time_taken')


# ---------- MAIN MODEL ADMINS ----------
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_short', 'category', 'topic', 'mark', 'isReadiness', 'created_at')
    list_filter = ('topic', 'isReadiness', 'created_at')
    search_fields = ('question', 'topic', 'category__title')
    inlines = [AnswerInline]
    ordering = ('-created_at',)

    def question_short(self, obj):
        return obj.question[:80] + ('...' if len(obj.question) > 80 else '')
    question_short.short_description = 'Question'


@admin.register(StudyModel)
class StudyModelAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'is_video', 'category', 'created_at')
    search_fields = ('title', 'content')
    list_filter = ('is_video', 'category')
    ordering = ('-created_at',)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('user', 'marks', 'total_marks', 'exam_mode', 'status', 'start_time', 'end_time')
    list_filter = ('exam_mode', 'status', 'start_time')
    search_fields = ('user__username',)
    inlines = [GivenQuizQuestionsInline]
    readonly_fields = ('start_time', 'end_time', 'marks', 'total_marks')

    fieldsets = (
        ('Quiz Info', {'fields': ('user', 'exam_mode', 'status', 'duration')}),
        ('Marks & Timing', {'fields': ('marks', 'total_marks', 'start_time', 'end_time')}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_marks', 'total_questions', 'total_time', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(StudyCategoryModel)
class StudyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_group', 'created_at')
    search_fields = ('name', 'plan_group__name')


@admin.register(StudyTopicModel)
class StudyTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'plan', 'category', 'created_at')
    search_fields = ('title', 'plan__name', 'category__name')
    list_filter = ('plan', 'category')


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'is_active', 'subscription_start_date', 'subscription_end_date', 'remaining_days_display')
    list_filter = ('is_active', 'plan', 'subscription_start_date')
    search_fields = ('user__username', 'plan')
    readonly_fields = ('subscription_start_date',)

    def remaining_days_display(self, obj):
        return obj.remaining_days()
    remaining_days_display.short_description = 'Days Left'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'school_name')
    search_fields = ('user__username', 'school_name')


# ---------- OPTIONAL ----------
# If you want to bulk-register small models without custom behavior:
admin.site.register(GivenQuizQuestions)
admin.site.register(Answer)
