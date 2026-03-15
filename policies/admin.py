from django.contrib import admin

from .models import Proposal, Policy, PolicyCoverage, PolicyDocument


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ['proposal_number', 'client', 'insurer', 'status', 'submission_date']
    list_filter = ['status', 'insurer']
    search_fields = ['proposal_number', 'client__name']
    raw_id_fields = ['client', 'broker']


class PolicyCoverageInline(admin.TabularInline):
    model = PolicyCoverage
    extra = 1


class PolicyDocumentInline(admin.TabularInline):
    model = PolicyDocument
    extra = 1


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ['policy_number', 'client', 'insurer', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'insurer', 'payment_method']
    search_fields = ['policy_number', 'client__name']
    raw_id_fields = ['client', 'broker']
    inlines = [PolicyCoverageInline, PolicyDocumentInline]


@admin.register(PolicyCoverage)
class PolicyCoverageAdmin(admin.ModelAdmin):
    list_display = ['policy', 'coverage', 'insured_amount', 'premium_amount']
    list_filter = ['coverage']


@admin.register(PolicyDocument)
class PolicyDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'policy', 'document_type', 'uploaded_by', 'created_at']
    list_filter = ['document_type']
