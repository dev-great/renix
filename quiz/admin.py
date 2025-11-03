from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, StudyCategoryModel, StudyTopicModel, StudyModel,
    Question, Answer, GivenQuizQuestions, Quiz, UserSubscription, UserProfile
)


# ---------- INLINE MODELS ----------
class AnswerInline(admin.StackedInline):
    model = Answer
    extra = 1
    show_change_link = True
    fields = ('answer', 'reason', 'is_correct')


class GivenQuizQuestionsInline(admin.TabularInline):
    model = GivenQuizQuestions
    extra = 0
    readonly_fields = ('question', 'answer', 'points', 'time_taken', 'created_at')
    can_delete = False


# ---------- CUSTOM FILTERS ----------
class IsCorrectFilter(admin.SimpleListFilter):
    title = 'Answer Correctness'
    parameter_name = 'is_correct'

    def lookups(self, request, model_admin):
        return (
            ('true', 'Correct Answers'),
            ('false', 'Incorrect Answers'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'true':
            return queryset.filter(is_correct=True)
        if self.value() == 'false':
            return queryset.filter(is_correct=False)
        return queryset


class ActiveSubscriptionFilter(admin.SimpleListFilter):
    title = 'Subscription Status'
    parameter_name = 'is_active'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('expired', 'Expired'),
        )

    def queryset(self, request, queryset):
        from django.utils import timezone
        if self.value() == 'active':
            return queryset.filter(is_active=True)
        if self.value() == 'inactive':
            return queryset.filter(is_active=False)
        if self.value() == 'expired':
            return queryset.filter(subscription_end_date__lt=timezone.now())
        return queryset


class QuizCompletionFilter(admin.SimpleListFilter):
    title = 'Completion Status'
    parameter_name = 'completion'

    def lookups(self, request, model_admin):
        return (
            ('completed', 'Completed'),
            ('in_progress', 'In Progress'),
            ('not_started', 'Not Started'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'completed':
            return queryset.filter(end_time__isnull=False)
        if self.value() == 'in_progress':
            return queryset.filter(end_time__isnull=True, given_question__isnull=False).distinct()
        if self.value() == 'not_started':
            return queryset.filter(given_question__isnull=True)
        return queryset


class TopicFilter(admin.SimpleListFilter):
    title = 'Topic'
    parameter_name = 'topic'

    def lookups(self, request, model_admin):
        return Question.objects.values_list('topic', 'topic').distinct()

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(topic=self.value())
        return queryset


# ---------- MAIN MODEL ADMINS ----------
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_preview', 'category', 'topic', 'mark', 'readiness_badge', 'created_at')
    list_filter = ('topic', 'isReadiness', 'category', 'mark', 'created_at')
    search_fields = ('question', 'topic', 'category__title')
    inlines = [AnswerInline]
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 50

    def question_preview(self, obj):
        preview = obj.question[:80] + ('...' if len(obj.question) > 80 else '')
        return format_html('<span title="{}">{}</span>', obj.question, preview)
    question_preview.short_description = 'Question'

    def readiness_badge(self, obj):
        if obj.isReadiness:
            return format_html('<span style="background-color: #417690; color: white; padding: 3px 8px; border-radius: 3px;">Readiness</span>')
        return format_html('<span style="background-color: #5cb85c; color: white; padding: 3px 8px; border-radius: 3px;">Regular</span>')
    readiness_badge.short_description = 'Type'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('answer_preview', 'question_short', 'correctness_badge', 'created_at')
    list_filter = (IsCorrectFilter, 'created_at', 'question__category')
    search_fields = ('answer', 'reason', 'question__question')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 50

    def answer_preview(self, obj):
        preview = obj.answer[:60] + ('...' if len(obj.answer) > 60 else '')
        return format_html('<span title="{}">{}</span>', obj.answer, preview)
    answer_preview.short_description = 'Answer'

    def question_short(self, obj):
        preview = obj.question.question[:50] + ('...' if len(obj.question.question) > 50 else '')
        return preview
    question_short.short_description = 'Question'

    def correctness_badge(self, obj):
        if obj.is_correct:
            return format_html('<span style="background-color: #5cb85c; color: white; padding: 3px 8px; border-radius: 3px;">✓ Correct</span>')
        return format_html('<span style="background-color: #d9534f; color: white; padding: 3px 8px; border-radius: 3px;">✗ Incorrect</span>')
    correctness_badge.short_description = 'Correctness'


@admin.register(StudyModel)
class StudyModelAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'category', 'video_badge', 'created_at')
    search_fields = ('title', 'content', 'topic__title', 'category__name')
    list_filter = ('is_video', 'category', 'topic', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 50

    def video_badge(self, obj):
        if obj.is_video:
            return format_html('<span style="background-color: #f0ad4e; color: white; padding: 3px 8px; border-radius: 3px;">🎥 Video</span>')
        return format_html('<span style="background-color: #5bc0de; color: white; padding: 3px 8px; border-radius: 3px;">📄 Text</span>')
    video_badge.short_description = 'Type'


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('user', 'score_display', 'mode_badge', 'completion_badge', 'start_time', 'duration_display')
    list_filter = ('exam_mode', 'status', 'start_time', QuizCompletionFilter)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    inlines = [GivenQuizQuestionsInline]
    readonly_fields = ('start_time', 'end_time', 'marks', 'total_marks')
    ordering = ('-start_time',)
    date_hierarchy = 'start_time'
    list_per_page = 50

    fieldsets = (
        ('Quiz Info', {'fields': ('user', 'exam_mode', 'status', 'duration')}),
        ('Marks & Timing', {'fields': ('marks', 'total_marks', 'start_time', 'end_time')}),
    )

    def score_display(self, obj):
        percentage = (obj.marks / obj.total_marks * 100) if obj.total_marks > 0 else 0
        color = '#5cb85c' if percentage >= 70 else '#f0ad4e' if percentage >= 50 else '#d9534f'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}/{} ({}%)</span>',
            color, obj.marks, obj.total_marks, int(percentage)
        )
    score_display.short_description = 'Score'

    def mode_badge(self, obj):
        if obj.exam_mode:
            return format_html('<span style="background-color: #d9534f; color: white; padding: 3px 8px; border-radius: 3px;">Exam</span>')
        return format_html('<span style="background-color: #5cb85c; color: white; padding: 3px 8px; border-radius: 3px;">Study</span>')
    mode_badge.short_description = 'Mode'

    def completion_badge(self, obj):
        if obj.end_time:
            return format_html('<span style="background-color: #5cb85c; color: white; padding: 3px 8px; border-radius: 3px;">✓ Completed</span>')
        if obj.given_question.exists():
            return format_html('<span style="background-color: #f0ad4e; color: white; padding: 3px 8px; border-radius: 3px;">⏳ In Progress</span>')
        return format_html('<span style="background-color: #ccc; color: black; padding: 3px 8px; border-radius: 3px;">Not Started</span>')
    completion_badge.short_description = 'Status'

    def duration_display(self, obj):
        if obj.start_time and obj.end_time:
            duration = (obj.end_time - obj.start_time).total_seconds() / 60
            return f'{int(duration)} min'
        return '—'
    duration_display.short_description = 'Duration'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_marks', 'total_questions', 'total_time', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    ordering = ('name',)
    date_hierarchy = 'created_at'


@admin.register(StudyCategoryModel)
class StudyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_group', 'created_at')
    search_fields = ('name', 'plan_group__name')
    list_filter = ('plan_group', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(StudyTopicModel)
class StudyTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'plan', 'category', 'created_at')
    search_fields = ('title', 'plan__name', 'category__name')
    list_filter = ('plan', 'category', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(GivenQuizQuestions)
class GivenQuizQuestionsAdmin(admin.ModelAdmin):
    list_display = ('quiz_user', 'question_preview', 'answer_preview', 'points', 'time_taken', 'created_at')
    list_filter = ('quiz__user', 'quiz__exam_mode', 'created_at')
    search_fields = ('quiz__user__username', 'question__question', 'answer__answer')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 50

    def quiz_user(self, obj):
        return obj.quiz.user.username
    quiz_user.short_description = 'User'

    def question_preview(self, obj):
        preview = obj.question.question[:50] + ('...' if len(obj.question.question) > 50 else '')
        return preview
    question_preview.short_description = 'Question'

    def answer_preview(self, obj):
        if obj.answer:
            preview = obj.answer.answer[:50] + ('...' if len(obj.answer.answer) > 50 else '')
            return format_html(
                '<span style="color: {};">✓</span> {}',
                '#5cb85c' if obj.answer.is_correct else '#d9534f',
                preview
            )
        return format_html('<span style="color: #ccc;">Not answered</span>')
    answer_preview.short_description = 'Answer'


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'plan', 'status_badge', 'subscription_start_date', 'subscription_end_date', 'remaining_days_display')
    list_filter = ('is_active', 'plan', 'subscription_start_date', ActiveSubscriptionFilter)
    search_fields = ('user__username', 'user__email', 'plan')
    readonly_fields = ('subscription_start_date',)
    ordering = ('-subscription_start_date',)
    date_hierarchy = 'subscription_start_date'
    list_per_page = 50

    def user_display(self, obj):
        return f'{obj.user.username} ({obj.user.email})'
    user_display.short_description = 'User'

    def status_badge(self, obj):
        from django.utils import timezone
        if obj.is_expired():
            return format_html('<span style="background-color: #d9534f; color: white; padding: 3px 8px; border-radius: 3px;">Expired</span>')
        if obj.is_active:
            return format_html('<span style="background-color: #5cb85c; color: white; padding: 3px 8px; border-radius: 3px;">Active</span>')
        return format_html('<span style="background-color: #ccc; color: black; padding: 3px 8px; border-radius: 3px;">Inactive</span>')
    status_badge.short_description = 'Status'

    def remaining_days_display(self, obj):
        days = obj.remaining_days()
        if days <= 0:
            return format_html('<span style="color: #d9534f; font-weight: bold;">Expired</span>')
        elif days <= 7:
            return format_html('<span style="color: #f0ad4e; font-weight: bold;">{} days</span>', days)
        return format_html('<span style="color: #5cb85c;">{} days</span>', days)
    remaining_days_display.short_description = 'Days Left'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'school_name', 'trial_badge')
    search_fields = ('user__username', 'user__email', 'school_name')
    list_filter = ('has_used_trial', 'user__date_joined')
    ordering = ('-user__date_joined',)
    date_hierarchy = 'user__date_joined'
    list_per_page = 50

    def user_display(self, obj):
        return f'{obj.user.get_full_name() or obj.user.username} ({obj.user.email})'
    user_display.short_description = 'User'

    def trial_badge(self, obj):
        if obj.has_used_trial:
            return format_html('<span style="background-color: #d9534f; color: white; padding: 3px 8px; border-radius: 3px;">Trial Used</span>')
        return format_html('<span style="background-color: #5cb85c; color: white; padding: 3px 8px; border-radius: 3px;">Trial Available</span>')
    trial_badge.short_description = 'Trial Status'