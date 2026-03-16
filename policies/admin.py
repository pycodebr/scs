from django.contrib import admin

from .models import Proposal, Policy, PolicyCoverage, PolicyDocument


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ['proposal_number', 'brokerage', 'client', 'insurer', 'status', 'submission_date']
    list_filter = ['brokerage', 'status', 'insurer']
    search_fields = ['proposal_number', 'client__name', 'brokerage__legal_name']
    autocomplete_fields = ['brokerage', 'client', 'broker', 'insurer', 'insurance_type']


class PolicyCoverageInline(admin.TabularInline):
    model = PolicyCoverage
    extra = 1
    autocomplete_fields = ['brokerage', 'coverage']


class PolicyDocumentInline(admin.TabularInline):
    model = PolicyDocument
    extra = 1
    autocomplete_fields = ['brokerage', 'uploaded_by']


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ['policy_number', 'brokerage', 'client', 'insurer', 'status', 'start_date', 'end_date']
    list_filter = ['brokerage', 'status', 'insurer', 'payment_method']
    search_fields = ['policy_number', 'client__name', 'brokerage__legal_name']
    autocomplete_fields = ['brokerage', 'proposal', 'client', 'broker', 'insurer', 'insurance_type']
    inlines = [PolicyCoverageInline, PolicyDocumentInline]


@admin.register(PolicyCoverage)
class PolicyCoverageAdmin(admin.ModelAdmin):
    list_display = ['policy', 'brokerage', 'coverage', 'insured_amount', 'premium_amount']
    list_filter = ['brokerage', 'coverage']
    autocomplete_fields = ['brokerage', 'policy', 'coverage']


@admin.register(PolicyDocument)
class PolicyDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'brokerage', 'policy', 'document_type', 'uploaded_by', 'created_at']
    list_filter = ['brokerage', 'document_type']
    autocomplete_fields = ['brokerage', 'policy', 'uploaded_by']
