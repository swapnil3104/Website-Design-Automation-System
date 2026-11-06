"""
backend/sitemap_app/page_planner.py
Page Planning Engine for Website Design Automation System.
Phase 4 & Phase 7 — AI Wireframe Generation Engine & Design Quality Optimization

Analyzes sitemap pages to determine purpose, section composition, section ordering,
content requirements, conversion goals, and global navigation consistency.
Enforces industry-specific heuristics, layout diversity, anti-repetition rules,
and responsive component selection across all 10 supported website categories.
"""

from __future__ import annotations
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import uuid

from .schemas.wireframe import (
    SUPPORTED_LAYOUT_VARIANTS,
    LAYOUT_VARIANT_ALIASES,
    CANONICAL_LUCIDE_ICONS,
)
from .schemas.sitemap import SECTION_TYPE_ALIASES, SUPPORTED_SECTION_TYPES


@dataclass
class PlannedSectionBlueprint:
    """Blueprint for a single section planned for a page."""
    id: str
    type: str
    title: str
    description: str
    layout_variant: str
    button_text: str = ""
    secondary_button_text: str = ""
    requires_items: bool = False
    items_count: int = 3
    order_index: int = 0


@dataclass
class PagePlan:
    """Complete structural and content plan for a single wireframe page."""
    page_name: str
    page_path: str
    page_id: str
    page_category: str
    purpose: str
    conversion_goals: List[str]
    primary_cta: str
    secondary_cta: str
    content_requirements: List[str]
    sections: List[PlannedSectionBlueprint]
    global_navigation: List[str]
    branding: Dict[str, Any] = field(default_factory=dict)
    website_category: str = 'business'


class PagePlanner:
    """
    Intelligent page planning service that translates sitemap hierarchy, brief,
    and industry category into detailed, conversion-focused wireframe blueprints.
    """

    # Canonical Supported Website Categories
    SUPPORTED_WEBSITE_CATEGORIES = [
        'business',
        'saas',
        'ecommerce',
        'portfolio',
        'agency',
        'healthcare',
        'education',
        'agriculture',
        'blog',
        'restaurant'
    ]

    # Complementary layout variants for intelligent anti-repetition alternation
    COMPLEMENTARY_LAYOUTS = {
        'layout-grid-3': ['layout-cards', 'layout-split', 'layout-list'],
        'layout-cards': ['layout-grid-3', 'layout-split', 'layout-list'],
        'layout-split': ['layout-grid-3', 'layout-cards', 'layout-centered'],
        'layout-split-right': ['layout-split-left', 'layout-cards', 'layout-grid-3'],
        'layout-split-left': ['layout-split-right', 'layout-cards', 'layout-grid-3'],
        'layout-grid-2': ['layout-cards', 'layout-split', 'layout-grid-3'],
        'layout-grid-4': ['layout-cards', 'layout-split', 'layout-grid-3'],
        'layout-list': ['layout-grid-3', 'layout-cards', 'layout-split'],
        'layout-centered': ['layout-split', 'layout-grid-3', 'layout-cards'],
        'layout-default': ['layout-split-right', 'layout-cards', 'layout-grid-3'],
        'layout-minimal': ['layout-cards', 'layout-split', 'layout-grid-3'],
        'layout-bold-text': ['layout-cards', 'layout-split-right', 'layout-grid-3'],
    }

    # Canonical Page Type Detection Matchers
    PAGE_TYPE_PATTERNS = [
        (r'\b(home|index|landing|welcome)\b', 'home'),
        (r'\b(about|story|who-we-are|mission|history)\b', 'about'),
        (r'\b(services|offerings|solutions|capabilities)\b', 'services'),
        (r'\b(service|solution|capability)[-_ ]?(detail|view)?\b', 'service-detail'),
        (r'\b(products|catalog|store|shop|produce|crops|dishes|menu)\b', 'products'),
        (r'\b(product|item|dish)[-_ ]?(detail|view)?\b', 'product-detail'),
        (r'\b(pricing|plans|subscription|rates|tier)\b', 'pricing'),
        (r'\b(contact|support|touch|reach|helpdesk|location|hours)\b', 'contact'),
        (r'\b(portfolio|work|projects|case[-_ ]?studies|gallery)\b', 'portfolio'),
        (r'\b(case[-_ ]?study|success[-_ ]?story)\b', 'case-study'),
        (r'\b(blog|news|articles|insights|posts|stories)\b', 'blog'),
        (r'\b(article|post|single[-_ ]?post)\b', 'blog-post'),
        (r'\b(faq|questions|help|knowledge[-_ ]?base)\b', 'faq'),
        (r'\b(careers|jobs|team|culture|hiring|faculty|doctors|staff)\b', 'careers'),
        (r'\b(search|find|booking[-_ ]?search|flight[-_ ]?search|reservations?)\b', 'booking-search'),
        (r'\b(results|search[-_ ]?results|flight[-_ ]?results)\b', 'booking-results'),
        (r'\b(checkout|payment|order)\b', 'checkout'),
        (r'\b(cart|bag|basket)\b', 'cart'),
        (r'\b(dashboard|portal|app|console)\b', 'dashboard'),
        (r'\b(account|settings|profile)\b', 'account-settings'),
        (r'\b(terms|tos|terms[-_ ]?of[-_ ]?service)\b', 'legal-terms'),
        (r'\b(privacy|policy|gdpr)\b', 'legal-privacy'),
        (r'\b(team|leadership|staff|instructors)\b', 'team'),
        (r'\b(testimonials|reviews|feedback)\b', 'testimonials'),
    ]

    # Category-Specific Tailored Page Blueprints
    CATEGORY_PAGE_BLUEPRINTS = {
        ('agriculture', 'home'): [
            ('navbar', 'Global Navigation', 'Agricultural brand header and farm navigation', 'layout-default', 'Wholesale Inquiry', ''),
            ('hero', 'Sustainable Agriculture & Certified Crop Harvests', 'Leading farm-to-table crop supply, regenerative farming techniques, and certified organic distribution.', 'layout-split-right', 'Inquire Wholesale', 'Explore Produce'),
            ('features', 'Seasonal Produce & Farm Capabilities', 'Certified organic fruits, vegetables, grains, and agronomy solutions grown under strict quality standards.', 'layout-grid-3', 'View Harvest Calendar', ''),
            ('process', 'Regenerative Farming & Supply Chain', 'From soil enrichment and precision irrigation to harvest cold-chain logistics with 100% farm origin traceability.', 'layout-cards', 'Learn Our Process', ''),
            ('stats', 'Harvest Scale & Environmental Metrics', 'Quantifiable impact metrics demonstrating farm acreage, annual yield, and sustainability scores.', 'layout-grid-4', '', ''),
            ('gallery', 'Farm Fields & Operational Facilities', 'High-resolution view into our automated greenhouses, open fields, and cold-chain sorting centers.', 'layout-grid-3', 'View Farm Facilities', ''),
            ('testimonial', 'Commercial Partner Endorsements', 'Feedback from supermarket procurement directors and regional food distribution cooperatives.', 'layout-cards', '', ''),
            ('cta', 'Partner With Our Harvest Operations', 'Secure steady, reliable commercial produce supplies with customized seasonal contracts.', 'layout-centered', 'Request Wholesale Catalog', ''),
            ('footer', 'Footer', 'Farm origin locations, organic certifications, and distributor resources.', 'layout-multi-column', 'Subscribe', '')
        ],
        ('restaurant', 'home'): [
            ('navbar', 'Global Navigation', 'Culinary restaurant navigation and table booking button', 'layout-default', 'Reserve Table', ''),
            ('hero', 'Artisan Dining & Culinary Excellence', 'Experience handcrafted seasonal dishes inspired by local heritage and contemporary gastronomy.', 'layout-centered', 'Reserve a Table', 'View Tasting Menu'),
            ('features', 'Signature Seasonal Menu', 'Chef curated tasting menus crafted with locally harvested organic ingredients and wine pairings.', 'layout-grid-3', 'Explore Full Menu', ''),
            ('story', 'Our Kitchen Philosophy & Heritage', 'Founded by award-winning culinary directors dedicated to zero-waste cooking and authentic traditions.', 'layout-split-left', 'Meet the Chefs', ''),
            ('gallery', 'Atmosphere & Culinary Creations', 'A visual journey through our warm dining room, private wine cellar, and signature culinary creations.', 'layout-cards', 'View Gallery', ''),
            ('testimonial', 'Guest & Food Critic Reviews', 'Acclaimed reviews from national gastronomy publications and delighted regular diners.', 'layout-grid-3', '', ''),
            ('contact-form', 'Table Reservations & Private Dining', 'Reserve your table online or book our private dining salon for exclusive celebrations.', 'layout-split-right', 'Confirm Reservation', ''),
            ('footer', 'Footer', 'Opening hours, valet parking, dining policies, and gift cards.', 'layout-multi-column', 'Join VIP Club', '')
        ],
        ('healthcare', 'home'): [
            ('navbar', 'Global Navigation', 'Healthcare clinic header with patient hotline and booking', 'layout-default', 'Book Appointment', ''),
            ('hero', 'Advanced Medical Care & Compassionate Support', 'Board-certified specialists delivering comprehensive diagnostics, modern treatments, and personalized patient care.', 'layout-split-right', 'Book Appointment', 'Find a Specialist'),
            ('services', 'Clinical Specialties & Departments', 'Expert care across cardiology, neurology, pediatrics, orthopedics, and emergency diagnostic medicine.', 'layout-cards', 'All Specialties', ''),
            ('features', 'Why Patients Trust Us', '24/7 emergency response, accredited diagnostic laboratories, and patient-first treatment plans.', 'layout-grid-3', 'Patient Standards', ''),
            ('team', 'Our Leading Physicians & Specialists', 'Meet our team of board-certified clinicians with decades of surgical and clinical experience.', 'layout-grid-3', 'View Full Directory', ''),
            ('stats', 'Clinical Excellence Metrics', 'Proven metrics showing patient recovery rates, surgical volume, and medical accreditations.', 'layout-grid-4', '', ''),
            ('contact-form', 'Schedule Your Consultation Today', 'Easily book an in-person or telehealth consultation with our specialist clinical team.', 'layout-split-left', 'Request Appointment', ''),
            ('faq', 'Patient FAQs & Insurance Info', 'Clear answers on accepted insurance providers, preparation for clinic visits, and medical records.', 'layout-list', '', ''),
            ('footer', 'Footer', 'Emergency telephone lines, hospital campus map, and patient rights policies.', 'layout-multi-column', 'Patient Portal', '')
        ],
        ('education', 'home'): [
            ('navbar', 'Global Navigation', 'Academic institution header with admissions button', 'layout-default', 'Apply for Admission', ''),
            ('hero', 'Empowering Minds, Shaping the Future', 'World-class academic programs, renowned faculty, and transformative research opportunities for the next generation.', 'layout-split-right', 'Apply for Admission', 'Explore Programs'),
            ('services', 'Academic Programs & Degrees', 'Undergraduate, graduate, and professional certification programs across technology, science, and the arts.', 'layout-cards', 'Browse Curriculum', ''),
            ('features', 'The Academic Advantage', 'Accredited curriculum, cutting-edge campus laboratories, and global study abroad partnerships.', 'layout-grid-3', 'Academic Excellence', ''),
            ('stats', 'Institutional Impact & Excellence', 'Key metrics demonstrating graduate employment, faculty-to-student ratios, and research grants.', 'layout-grid-4', '', ''),
            ('testimonial', 'Alumni & Student Success Stories', 'Hear from graduates making breakthrough contributions across industry and academia.', 'layout-grid-3', '', ''),
            ('cta', 'Begin Your Academic Journey Today', 'Applications are now open for the upcoming academic semester. Financial aid and scholarships available.', 'layout-centered', 'Start Application', ''),
            ('footer', 'Footer', 'Academic calendar, accreditation notices, admissions office, and student portal.', 'layout-multi-column', 'Request Prospectus', '')
        ],
        ('ecommerce', 'home'): [
            ('navbar', 'Global Navigation', 'E-commerce store header with search, cart, and account links', 'layout-default', 'Cart (0)', ''),
            ('hero', 'Discover Premium Quality Products', 'Curated collections of premium essentials designed for modern living. Fast shipping and satisfaction guaranteed.', 'layout-split-right', 'Shop New Arrivals', 'Browse Best Sellers'),
            ('product-grid', 'Trending & Best Sellers', 'Explore our highest rated products with verified customer reviews and instant checkout options.', 'layout-grid-3', 'Shop Collection', ''),
            ('features', 'The Customer Guarantee', 'Complimentary carbon-neutral shipping on orders over $50, 30-day hassle-free returns, and 24/7 support.', 'layout-cards', '', ''),
            ('promo', 'Limited Time Seasonal Offer', 'Enjoy up to 25% off selected catalog items during our seasonal showcase. Use code SEASONAL at checkout.', 'layout-centered', 'Claim Offer', ''),
            ('testimonial', 'Verified Buyer Reviews', 'Real feedback from satisfied customers who love the quality, durability, and aesthetics of our products.', 'layout-grid-3', '', ''),
            ('cta', 'Subscribe & Save 15% On Your First Order', 'Be the first to know about exclusive drops, secret sales, and subscriber-only discounts.', 'layout-centered', 'Get Discount Code', ''),
            ('footer', 'Footer', 'Order tracking, return portal, shipping policies, customer support, and payment options.', 'layout-multi-column', 'Track Order', '')
        ],
        ('saas', 'home'): [
            ('navbar', 'Global Navigation', 'SaaS platform header with login and free trial action', 'layout-default', 'Start Free Trial', ''),
            ('hero', 'Automate Your Workflow, Scale Your Product', 'The intelligent platform designed for modern product teams to build, deploy, and monitor scalable software seamlessly.', 'layout-split-right', 'Start Free 14-Day Trial', 'Schedule Live Demo'),
            ('features', 'Engineered for Performance & Scale', 'Automated workflows, end-to-end encryption, real-time collaboration, and enterprise grade reliability.', 'layout-grid-3', 'Explore Architecture', ''),
            ('main-info', 'Deep Platform Integration & Developer APIs', 'Connect your existing tech stack with 100+ native integrations and robust REST and GraphQL APIs.', 'layout-split', 'View Developer Docs', ''),
            ('stats', 'Proven Enterprise Reliability', 'Guaranteed uptime SLA, hundreds of millions of daily API transactions, and global low-latency nodes.', 'layout-grid-4', '', ''),
            ('pricing', 'Predictable, Scalable Pricing Plans', 'Flexible plans tailored for early-stage startups to global enterprise engineering teams.', 'layout-grid-3', 'Select Tier', ''),
            ('testimonial', 'Trusted by Leading Tech Teams', 'See how top engineering and product leaders reduced cycle times by 65% with our platform.', 'layout-cards', '', ''),
            ('faq', 'Frequently Asked Questions', 'Common questions about security compliance, billing, data migration, and enterprise SLAs.', 'layout-list', '', ''),
            ('cta', 'Ready to Accelerate Your Team?', 'Join over 10,000 engineering teams delivering better software faster. No credit card required.', 'layout-centered', 'Get Started Now', ''),
            ('footer', 'Footer', 'Documentation, API status, security reports, changelog, and developer community.', 'layout-multi-column', 'Subscribe', '')
        ],
        ('portfolio', 'home'): [
            ('navbar', 'Global Navigation', 'Minimalist creative header with contact action', 'layout-default', 'Hire Me', ''),
            ('hero', 'Visual Designer & Creative Developer', 'Crafting memorable digital experiences, brand identities, and design systems for forward-thinking brands worldwide.', 'layout-minimal', 'View Selected Works', 'Download CV'),
            ('gallery', 'Selected Works & Case Studies', 'Curated showcase of commercial and experimental projects spanning UI/UX, 3D, and interactive art.', 'layout-grid-3', 'View Case Study', ''),
            ('features', 'Core Disciplines & Capabilities', 'User experience design, creative coding, design tokens, responsive web development, and brand strategy.', 'layout-cards', '', ''),
            ('about', 'Design Philosophy & Background', 'Over a decade of experience blending human-centered design with rigorous engineering execution.', 'layout-split', 'Read Full Bio', ''),
            ('testimonial', 'Client & Collaborator Words', 'Kind words and recommendations from design directors, startup founders, and engineering leads.', 'layout-grid-2', '', ''),
            ('contact', 'Have a Project in Mind?', 'Currently accepting select freelance inquiries, design advising, and speaking engagements for 2026.', 'layout-centered', 'Let’s Collaborate', ''),
            ('footer', 'Footer', 'Social links, colophon, copyright, and availability calendar.', 'layout-multi-column', 'Email Me', '')
        ],
        ('agency', 'home'): [
            ('navbar', 'Global Navigation', 'Agency header with work inquiry CTA', 'layout-default', 'Work With Us', ''),
            ('hero', 'We Build Brands That Define Tomorrow', 'Full-service digital agency partnering with ambitious companies to create unforgettable identities and digital products.', 'layout-bold-text', 'Start a Project', 'Explore Showreel'),
            ('gallery', 'Featured Client Work & Case Studies', 'Award-winning digital experiences, brand transformations, and high-conversion commercial launches.', 'layout-grid-3', 'View Case Study', ''),
            ('services', 'Strategic Capabilities', 'Brand Strategy, Full-Stack Web Development, UI/UX Systems, Growth Marketing, and Content Production.', 'layout-cards', 'All Capabilities', ''),
            ('process', 'Our Collaborative Sprint Process', 'A battle-tested 4-step framework: Discovery, Strategic Prototyping, Execution, and Growth Optimization.', 'layout-split', 'Our Methodology', ''),
            ('stats', 'Measurable Client Results', 'Global design awards won, average revenue lift delivered, and venture funding raised by clients.', 'layout-grid-4', '', ''),
            ('testimonial', 'What Founders & CMOs Say', 'Authentic endorsements from leaders who trusted us with their core brand identity and digital presence.', 'layout-cards', '', ''),
            ('cta', 'Let’s Create Something Exceptional Together', 'Ready to elevate your market position? Tell us about your goals and schedule a strategic discovery session.', 'layout-centered', 'Book Discovery Session', ''),
            ('footer', 'Footer', 'Studio offices, careers, press inquiries, and client portal.', 'layout-multi-column', 'Get in Touch', '')
        ],
        ('blog', 'home'): [
            ('navbar', 'Global Navigation', 'Editorial publication header with topics and newsletter CTA', 'layout-default', 'Subscribe', ''),
            ('hero', 'Frontiers of Technology, Design & Culture', 'Authoritative analysis, in-depth technical essays, and insightful interviews with industry leaders.', 'layout-split-right', 'Read Featured Story', 'Browse Topics'),
            ('features', 'Trending & Editor’s Choice', 'Hand-picked essays and investigative pieces generating wide conversation across the industry.', 'layout-grid-3', 'Read Article', ''),
            ('main-info', 'Latest Published Articles', 'Chronological feed with estimated reading times, category tags, and author bylines.', 'layout-list', 'Load More Stories', ''),
            ('team', 'Contributing Writers & Editors', 'Meet the journalists, researchers, and technical writers behind our publications.', 'layout-grid-4', 'View Author Bios', ''),
            ('cta', 'Delivered Straight to Your Inbox Every Week', 'Join 75,000+ professionals receiving our curated briefing with zero advertising spam.', 'layout-centered', 'Subscribe Free', ''),
            ('footer', 'Footer', 'Editorial guidelines, archives, RSS feed, pitch guidelines, and masthead.', 'layout-multi-column', 'Newsletter', '')
        ],
        ('business', 'home'): [
            ('navbar', 'Global Navigation', 'Corporate enterprise header with consultation button', 'layout-default', 'Contact Sales', ''),
            ('hero', 'Strategic Solutions for Modern Enterprise', 'Empowering global organizations with specialized consulting, financial advisory, and technology transformation.', 'layout-split-right', 'Schedule Consultation', 'View Capabilities'),
            ('services', 'Core Enterprise Solutions', 'Management consulting, digital infrastructure, risk management, and operational efficiency programs.', 'layout-cards', 'Explore Solutions', ''),
            ('main-info', 'Our Proven Transformation Methodology', 'Structured corporate engagements driven by data intelligence, cross-functional collaboration, and measurable ROI.', 'layout-split', 'Read Methodology', ''),
            ('stats', 'Global Corporate Scale', 'Measurable enterprise value delivered, successful engagements completed, and global offices.', 'layout-grid-4', '', ''),
            ('testimonial', 'Enterprise Client Endorsements', 'Insights from Fortune 500 executives who partnered with our firm to accelerate market leadership.', 'layout-grid-3', '', ''),
            ('cta', 'Accelerate Your Enterprise Objectives', 'Connect with our senior partners to explore how customized strategies can drive sustainable profitability.', 'layout-centered', 'Request Executive Consultation', ''),
            ('footer', 'Footer', 'Investor relations, regulatory compliance, global office locations, and annual reports.', 'layout-multi-column', 'Contact Firm', '')
        ],
    }

    # Canonical Default Section Blueprints per Page Type (Fallback)
    CANONICAL_PAGE_BLUEPRINTS = {
        'home': [
            ('navbar', 'Global Navigation', 'Primary brand header and top navigation', 'layout-default', 'Contact Us', ''),
            ('hero', 'Welcome Hero', 'Compelling headline communicating unique value proposition and trial CTA', 'layout-split-right', 'Get Started', 'Learn More'),
            ('features', 'Core Capabilities', 'Three key architectural features highlighting scalability and ease of use', 'layout-grid-3', 'Explore Features', ''),
            ('main-info', 'Deep Dive & Differentiation', 'Technical explanation of how the platform solves major customer pain points', 'layout-split', 'View Solutions', ''),
            ('testimonial', 'Client Social Proof', 'Customer quotes and quantitative proof points from industry leaders', 'layout-cards', 'Read Stories', ''),
            ('cta', 'Call to Action', 'Focused high-conversion banner driving registration or inquiry', 'layout-centered', 'Get Started Now', ''),
            ('footer', 'Footer', 'Multi-column navigational links, legal, and company resources', 'layout-multi-column', 'Subscribe', '')
        ],
        'about': [
            ('navbar', 'Global Navigation', 'Primary brand header and top navigation', 'layout-default', 'Contact Us', ''),
            ('hero', 'Our Mission & Story', 'Introduction to company founding, vision, and core principles', 'layout-centered', 'Join Our Mission', ''),
            ('story', 'Our Growth Journey', 'Chronological milestones illustrating company evolution and track record', 'layout-list', 'Learn More', ''),
            ('values', 'Guiding Values', 'Core operating standards and ethical principles guiding team execution', 'layout-grid-3', '', ''),
            ('team', 'Leadership Team', 'Executive profiles and key leaders with background summaries', 'layout-cards', 'Join the Team', ''),
            ('stats', 'Impact in Numbers', 'Key metrics demonstrating global scale and user satisfaction', 'layout-grid-4', '', ''),
            ('cta', 'Build With Us', 'Invitation to partner with or join our growing organization', 'layout-centered', 'Get in Touch', ''),
            ('footer', 'Footer', 'Comprehensive footer links and company details', 'layout-multi-column', 'Subscribe', '')
        ],
        'services': [
            ('navbar', 'Global Navigation', 'Primary brand header and top navigation', 'layout-default', 'Contact Us', ''),
            ('hero', 'Professional Services Overview', 'High-impact overview of commercial services and customer results', 'layout-split-right', 'Request Consultation', 'View Catalog'),
            ('services', 'Core Offerings Grid', 'Detailed overview of individual service tiers and specialized capabilities', 'layout-cards', 'Learn More', ''),
            ('main-info', 'Our Methodology & Process', 'Step-by-step engagement process explaining discovery, execution, and delivery', 'layout-split', 'Our Approach', ''),
            ('pricing', 'Service Engagements & Pricing', 'Transparent pricing packages and scope commitments', 'layout-grid-3', 'Select Tier', ''),
            ('testimonial', 'Client Endorsements', 'Testimonials from partners who scaled their operations using our services', 'layout-cards', '', ''),
            ('cta', 'Ready to Transform Your Workflow?', 'Schedule a discovery call with a dedicated senior specialist', 'layout-centered', 'Schedule Consultation', ''),
            ('footer', 'Footer', 'Footer with contact information and service resources', 'layout-multi-column', 'Subscribe', '')
        ],
        'service-detail': [
            ('navbar', 'Global Navigation', 'Primary brand header and top navigation', 'layout-default', 'Contact Us', ''),
            ('hero', 'Specialized Service Deep Dive', 'Specific service value proposition, deliverables, and business benefits', 'layout-split-right', 'Request Quote', ''),
            ('main-info', 'Scope & Deliverables', 'Comprehensive breakdown of technical deliverables and timeline expectations', 'layout-split', '', ''),
            ('features', 'Included Capabilities', 'Grid of features and operational tools included with this service', 'layout-grid-3', '', ''),
            ('faq', 'Service FAQs', 'Answers to common questions regarding timelines, dependencies, and billing', 'layout-list', '', ''),
            ('cta', 'Kickstart This Service', 'Direct conversion route to request an estimate or onboard immediately', 'layout-centered', 'Get Started', ''),
            ('footer', 'Footer', 'Global footer', 'layout-multi-column', '', '')
        ],
        'pricing': [
            ('navbar', 'Global Navigation', 'Primary brand header and top navigation', 'layout-default', 'Contact Us', ''),
            ('hero', 'Simple, Transparent Pricing', 'Predictable pricing tiers designed to scale with your team and needs', 'layout-centered', 'Compare Plans', ''),
            ('pricing', 'Subscription Plans', 'Three tier comparison grid with prices, features, and action buttons', 'layout-grid-3', 'Select Plan', ''),
            ('main-info', 'Enterprise Capabilities', 'Custom infrastructure, dedicated SLAs, and enterprise security features', 'layout-split', 'Contact Enterprise Sales', ''),
            ('faq', 'Frequently Asked Questions', 'Clear answers on billing, upgrade policies, refunds, and cancellation', 'layout-list', '', ''),
            ('cta', 'Need a Custom Plan?', 'Talk to our solutions engineering team for customized high-volume licensing', 'layout-centered', 'Contact Sales', ''),
            ('footer', 'Footer', 'Footer with billing and terms links', 'layout-multi-column', '', '')
        ],
        'contact': [
            ('navbar', 'Global Navigation', 'Primary brand header and top navigation', 'layout-default', 'Contact Us', ''),
            ('hero', 'Get in Touch', 'Direct channels to reach our sales, support, and partnership teams', 'layout-centered', '', ''),
            ('contact-form', 'Direct Inquiry Form', 'Interactive form for messages, technical inquiries, and consultation bookings', 'layout-split-left', 'Send Message', ''),
            ('contact-details', 'Office & Direct Details', 'Physical addresses, email routes, phone numbers, and operational hours', 'layout-cards', '', ''),
            ('faq', 'Quick Support Answers', 'Immediate answers to common pre-sales and technical questions', 'layout-list', '', ''),
            ('footer', 'Footer', 'Global navigation footer', 'layout-multi-column', '', '')
        ],
        'portfolio': [
            ('navbar', 'Global Navigation', 'Primary brand header and top navigation', 'layout-default', 'Contact Us', ''),
            ('hero', 'Featured Work & Projects', 'Curated visual showcase of delivered work, client metrics, and client outcomes', 'layout-centered', 'View Case Studies', ''),
            ('gallery', 'Project Showcase Grid', 'Visual grid of past client engagements with categorized filter tabs', 'layout-grid-3', 'View Project', ''),
            ('stats', 'Project Milestones & Impact', 'Quantitative metrics showing client revenue uplift and performance gains', 'layout-grid-4', '', ''),
            ('testimonial', 'Client Reviews', 'Quotes from founders and product leads regarding project collaboration', 'layout-cards', '', ''),
            ('cta', 'Start Your Next Project', 'Let us turn your design vision into an exceptional web experience', 'layout-centered', 'Discuss Your Project', ''),
            ('footer', 'Footer', 'Global footer', 'layout-multi-column', '', '')
        ],
        'blog': [
            ('navbar', 'Global Navigation', 'Primary brand header and top navigation', 'layout-default', 'Contact Us', ''),
            ('hero', 'Insights & Industry Trends', 'Editorial publication covering modern development, design, and architecture', 'layout-centered', 'Browse Categories', ''),
            ('features', 'Featured Articles', 'Lead article highlights and editor choices with reading time badges', 'layout-grid-3', 'Read Article', ''),
            ('main-info', 'Latest Publications', 'Chronological archive of articles with category filtering and search', 'layout-list', 'Load More', ''),
            ('cta', 'Join Our Newsletter', 'Receive weekly strategic insights directly in your inbox without spam', 'layout-centered', 'Subscribe Free', ''),
            ('footer', 'Footer', 'Global footer with editorial links', 'layout-multi-column', '', '')
        ],
        'faq': [
            ('navbar', 'Global Navigation', 'Primary brand header and top navigation', 'layout-default', 'Contact Us', ''),
            ('hero', 'Help & Frequently Asked Questions', 'Quick search and comprehensive answers across setup, billing, and features', 'layout-centered', '', ''),
            ('faq', 'General & Setup FAQs', 'Categorized questions and answers regarding platform capabilities', 'layout-list', '', ''),
            ('contact', 'Still Have Questions?', 'Direct links to speak with a human support specialist or join our Discord', 'layout-split', 'Contact Support', ''),
            ('footer', 'Footer', 'Global footer', 'layout-multi-column', '', '')
        ],
        'booking-search': [
            ('navbar', 'Global Navigation', 'Primary brand header and top navigation', 'layout-default', 'My Bookings', ''),
            ('hero', 'Search Flights & Travel', 'Search header with destination selector, date picker, and fare options', 'layout-centered', 'Search Options', ''),
            ('promo', 'Special Offers & Routes', 'Seasonal discounts and featured destinations with special rates', 'layout-cards', 'Book Now', ''),
            ('features', 'Why Fly With Us', 'Flexible cancellations, onboard amenities, and punctuality records', 'layout-grid-3', '', ''),
            ('testimonial', 'Traveler Reviews', 'Stories and high ratings from frequent flyers and vacation travelers', 'layout-cards', '', ''),
            ('footer', 'Footer', 'Global footer with airline policies and terms', 'layout-multi-column', '', '')
        ],
        'generic': [
            ('navbar', 'Global Navigation', 'Primary brand header and top navigation', 'layout-default', 'Contact Us', ''),
            ('hero', 'Page Header', 'Clear headline explaining page purpose and contextual background', 'layout-split-right', 'Learn More', ''),
            ('main-info', 'Core Information', 'Structured content detailing core objectives and functional topics', 'layout-split', '', ''),
            ('features', 'Key Highlights', 'Three column highlights grid showcasing benefits and capabilities', 'layout-grid-3', '', ''),
            ('cta', 'Next Steps', 'Call to action encouraging the visitor to explore further or reach out', 'layout-centered', 'Get in Touch', ''),
            ('footer', 'Footer', 'Global navigation footer', 'layout-multi-column', '', '')
        ]
    }

    # Ordering Hierarchy Weights: Navbar is always 0, Hero is 10, Footer is 100
    SECTION_ORDER_WEIGHTS = {
        'navbar': 0,
        'hero': 10,
        'promo': 15,
        'booking-search': 18,
        'search-form': 18,
        'features': 25,
        'services': 25,
        'services-grid': 25,
        'product-grid': 25,
        'main-info': 30,
        'about': 30,
        'story': 32,
        'values': 34,
        'pricing': 40,
        'pricing-table': 40,
        'supporting-info': 45,
        'process': 48,
        'stats': 50,
        'team': 55,
        'gallery': 58,
        'testimonial': 60,
        'trust': 62,
        'case-study': 65,
        'faq': 70,
        'contact': 75,
        'contact-form': 75,
        'contact-details': 78,
        'cta': 90,
        'footer': 100,
    }

    def detect_website_category(self, sitemap_data: Dict[str, Any]) -> str:
        """
        Extracts and normalizes the website category into one of the 10 canonical categories:
        business, saas, ecommerce, portfolio, agency, healthcare, education, agriculture, blog, restaurant.
        """
        if not isinstance(sitemap_data, dict):
            return 'business'

        brief = sitemap_data.get('brief') if isinstance(sitemap_data.get('brief'), dict) else {}
        explicit_cat = str(brief.get('category') or brief.get('type') or '').lower().strip()
        if explicit_cat in self.SUPPORTED_WEBSITE_CATEGORIES:
            return explicit_cat

        web_type = str(sitemap_data.get('website_type') or brief.get('type') or brief.get('category') or '').lower()

        # Keyword mapping to canonical categories
        category_signatures = [
            ('agriculture', ['agriculture', 'farm', 'farming', 'crops', 'produce', 'agtech', 'harvest', 'organic', 'livestock', 'cultivation', 'orchard', 'ranch']),
            ('restaurant', ['restaurant', 'dining', 'food', 'cafe', 'bistro', 'culinary', 'bakery', 'bar', 'chef', 'menu', 'catering']),
            ('healthcare', ['healthcare', 'health', 'hospital', 'clinic', 'medical', 'doctor', 'patient', 'dental', 'therapy', 'telehealth', 'wellness']),
            ('education', ['education', 'school', 'university', 'college', 'academy', 'course', 'learning', 'training', 'student', 'tutor', 'bootcamp', 'curriculum']),
            ('ecommerce', ['ecommerce', 'e-commerce', 'shop', 'store', 'cart', 'checkout', 'products', 'apparel', 'merchandise', 'retail', 'buy online']),
            ('portfolio', ['portfolio', 'designer', 'freelancer', 'artist', 'photographer', 'developer', 'resume', 'cv', 'personal brand']),
            ('agency', ['agency', 'creative studio', 'marketing', 'advertising', 'branding', 'design agency', 'pr agency', 'digital agency']),
            ('blog', ['blog', 'magazine', 'editorial', 'journal', 'news', 'articles', 'publishing', 'media', 'publication']),
            ('saas', ['saas', 'software', 'cloud app', 'b2b tool', 'dashboard app', 'devops tool', 'workflow automation']),
            ('business', ['business', 'corporate', 'consulting', 'advisory', 'firm', 'financial', 'insurance', 'logistics', 'b2b', 'enterprise'])
        ]

        for cat_id, keywords in category_signatures:
            if cat_id in web_type or any(kw in web_type for kw in keywords):
                return cat_id

        return 'business'

    def detect_page_category(self, page_name: str, description: str = "") -> str:
        """Detect the canonical page category from the page title and description."""
        combined = f"{page_name} {description}".lower()
        for pattern, cat in self.PAGE_TYPE_PATTERNS:
            if re.search(pattern, combined):
                return cat
        return 'generic'

    def get_category_page_blueprint(self, website_category: str, page_category: str) -> List[Tuple]:
        """
        Retrieves the most specific blueprint sequence:
        1. (website_category, page_category)
        2. (website_category, 'home') if page_category is 'home'
        3. CANONICAL_PAGE_BLUEPRINTS[page_category]
        4. CANONICAL_PAGE_BLUEPRINTS['generic']
        """
        key = (website_category, page_category)
        if key in self.CATEGORY_PAGE_BLUEPRINTS:
            return self.CATEGORY_PAGE_BLUEPRINTS[key]

        if page_category == 'home':
            home_key = (website_category, 'home')
            if home_key in self.CATEGORY_PAGE_BLUEPRINTS:
                return self.CATEGORY_PAGE_BLUEPRINTS[home_key]

        if page_category in self.CANONICAL_PAGE_BLUEPRINTS:
            return self.CANONICAL_PAGE_BLUEPRINTS[page_category]

        return self.CANONICAL_PAGE_BLUEPRINTS['generic']

    def enforce_layout_diversity(self, sections: List[PlannedSectionBlueprint]) -> List[PlannedSectionBlueprint]:
        """
        Anti-Repetition & Layout Diversity Engine:
        1. Ensures no two adjacent sections share the exact same layoutVariant.
        2. Replaces consecutive duplicate section types with appropriate complementary types.
        3. Ensures item counts fit responsive grid break guidelines.
        """
        if not sections or len(sections) < 2:
            return sections

        diversified: List[PlannedSectionBlueprint] = []

        for i, current in enumerate(sections):
            # Skip modifying navbar (index 0) or footer (last)
            if current.type in ('navbar', 'footer'):
                diversified.append(current)
                continue

            prev = diversified[-1] if diversified else None

            # 1. Anti-repetition: Prevent identical adjacent section types
            if prev and prev.type == current.type and current.type not in ('main-info', 'supporting-info'):
                # Alternate type to a complementary one
                type_alternatives = {
                    'features': 'process',
                    'services': 'features',
                    'testimonial': 'stats',
                    'stats': 'testimonial',
                    'gallery': 'features',
                    'cta': 'main-info'
                }
                new_type = type_alternatives.get(current.type, 'main-info')
                current.type = new_type
                current.title = f"{current.title} — Overview"

            # 2. Anti-repetition: Prevent identical adjacent layout variants
            if prev and prev.layout_variant == current.layout_variant:
                candidates = self.COMPLEMENTARY_LAYOUTS.get(current.layout_variant, ['layout-cards', 'layout-split', 'layout-grid-3'])
                next_layout = sections[i + 1].layout_variant if i + 1 < len(sections) else None

                # Choose the first candidate that doesn't match prev or next layout
                selected_layout = None
                for cand in candidates:
                    if cand != prev.layout_variant and cand != next_layout:
                        selected_layout = cand
                        break

                current.layout_variant = selected_layout or candidates[0]

            # 3. Responsive items count enforcement
            if current.requires_items:
                if current.layout_variant == 'layout-grid-4':
                    current.items_count = 4
                elif current.layout_variant in ('layout-grid-3', 'layout-cards'):
                    current.items_count = 3
                elif current.layout_variant == 'layout-grid-2':
                    current.items_count = 2

            diversified.append(current)

        return diversified

    def extract_global_navigation(self, sitemap_data: Dict[str, Any]) -> List[str]:
        """
        Extract primary navigation menu items from the sitemap page hierarchy.
        Ensures consistent navbar links across all generated wireframe pages.
        """
        items: List[str] = []

        def collect(pages: List[Dict[str, Any]]):
            for p in pages or []:
                if not isinstance(p, dict):
                    continue
                name = str(p.get('name') or '').strip()
                if name and name not in items:
                    items.append(name)
                # Cap navigation links to 6 top-level items for clean presentation
                if len(items) >= 6:
                    return

        pages = sitemap_data.get('pages', []) if isinstance(sitemap_data, dict) else []
        collect(pages)

        # Fallback to standard navigation links if none extracted
        if len(items) < 3:
            default_links = ['Home', 'About', 'Services', 'Pricing', 'Contact']
            for dl in default_links:
                if dl not in items:
                    items.append(dl)
                if len(items) >= 5:
                    break

        return items[:6]

    def _determine_page_purpose(self, page_name: str, category: str, website_category: str, brief: Dict[str, Any]) -> str:
        """Formulate a specific, conversion-oriented purpose statement tailored to the website category."""
        client = str(brief.get('client') or 'the brand').strip()
        type_str = str(brief.get('type') or f'{website_category.title()} Website').strip()

        # Category-specific purpose statements
        if website_category == 'agriculture':
            if category == 'home':
                return f"Showcase {client}'s certified sustainable harvest operations, farm-to-table supply reliability, and drive bulk wholesale contract inquiries."
            return f"Highlight agricultural capabilities and certified produce standards in support of {client}'s commercial supply goals."

        if website_category == 'restaurant':
            if category == 'home':
                return f"Introduce {client}'s artisan culinary philosophy, showcase seasonal menu highlights, and facilitate direct online table reservations."
            return f"Present culinary details and dining atmosphere to guide guest reservations and private event bookings."

        if website_category == 'healthcare':
            if category == 'home':
                return f"Build immediate clinical trust, present medical specialties, and provide a frictionless pathway to book patient consultations."
            return f"Deliver clear patient guidance, clinical credentials, and direct consultation booking routes for {client}."

        if website_category == 'education':
            if category == 'home':
                return f"Present accredited academic programs, faculty credentials, and inspire prospective students to submit enrollment applications."
            return f"Provide comprehensive curriculum details and admissions instructions for prospective students at {client}."

        if website_category == 'ecommerce':
            if category == 'home':
                return f"Inspire product discovery, showcase trending bestsellers, and maximize instant cart additions and checkout conversions."
            return f"Streamline product evaluation and purchase confidence across {client}'s catalog."

        if website_category == 'saas':
            if category == 'home':
                return f"Articulate {client}'s core software value proposition, demonstrate workflow automation, and acquire self-serve trial signups."
            return f"Clarify platform architecture, integration capabilities, and pricing to facilitate SaaS conversion."

        if website_category == 'portfolio':
            if category == 'home':
                return f"Showcase {client}'s signature creative craftsmanship, design rationale, and attract high-value commissions or hiring offers."
            return f"Provide deep case study context and interactive project breakdowns."

        if website_category == 'agency':
            if category == 'home':
                return f"Demonstrate award-winning digital capabilities, client ROI metrics, and drive strategic project kickoff inquiries."
            return f"Present agency service capabilities and collaborative sprint methodology."

        if website_category == 'blog':
            if category == 'home':
                return f"Deliver authoritative journalism and technical essays to maximize readership, engagement, and newsletter subscribers."
            return f"Organize editorial publications by topic and author to foster sustained readership."

        # Default business purpose
        if category == 'home':
            return f"Welcome visitors to {client}, articulate the corporate value proposition of {type_str}, and drive primary conversion to executive consultation."

        purposes = {
            'about': f"Build authority and trust by sharing {client}'s founding story, mission, leadership credentials, and corporate values.",
            'services': f"Detail the commercial service offerings, deliverables, and engagement tiers provided by {client}.",
            'service-detail': f"Provide an in-depth breakdown of technical scope, methodology, and ROI for this specific service.",
            'pricing': f"Present transparent, scalable pricing packages with clear feature distinctions to facilitate purchase decisions.",
            'contact': f"Provide friction-free inquiry channels, direct contact information, and consultation booking for prospective clients.",
            'portfolio': f"Showcase proven deliverables, client metrics, and visual project work demonstrating past success.",
            'blog': f"Deliver authoritative industry insights and educational content to attract organic traffic and foster subscriber loyalty.",
            'faq': f"Eliminate customer purchase friction by resolving top technical, commercial, and operational questions.",
            'booking-search': f"Empower visitors to quickly search, compare, and reserve flight or travel arrangements.",
        }
        return purposes.get(category, f"Present structured information regarding {page_name} in support of {client}'s business objectives.")

    def _determine_conversion_goals(self, category: str, website_category: str, brief: Dict[str, Any]) -> List[str]:
        """Determine primary and secondary conversion goals tailored to the website category."""
        category_goals = {
            'agriculture': ['Submit wholesale harvest inquiry', 'Download seasonal produce catalog', 'Schedule farm tour or facility inspection'],
            'restaurant': ['Reserve a dining table online', 'Inquire for private dining salon event', 'View seasonal tasting menu with wine pairings'],
            'healthcare': ['Schedule in-person or telehealth appointment', 'Find a qualified board-certified specialist', 'Access 24/7 patient emergency assistance'],
            'education': ['Submit online application for admission', 'Download program curriculum syllabus', 'Book virtual campus tour'],
            'ecommerce': ['Complete online purchase checkout', 'Add trending product to bag', 'Subscribe for 15% first-order discount'],
            'saas': ['Start 14-day free product trial', 'Schedule live interactive product demo', 'Explore API documentation & integrations'],
            'portfolio': ['Schedule freelance or contract consultation', 'Review full interactive case study', 'Download design resume / CV'],
            'agency': ['Submit project scoping inquiry', 'Schedule strategic discovery session', 'Review client case study showreel'],
            'blog': ['Subscribe to weekly email briefing', 'Read featured editorial analysis', 'Share article on professional networks'],
            'business': ['Schedule executive consultation', 'Request corporate RFP proposal', 'Download enterprise capability whitepaper']
        }

        if category == 'home' and website_category in category_goals:
            return category_goals[website_category]

        page_goals_map = {
            'about': ['Learn about company vision and milestones', 'View leadership credentials', 'Explore career openings'],
            'services': ['Request customized service proposal', 'Select standard engagement package', 'Schedule consultation'],
            'pricing': ['Select subscription or service plan', 'Contact enterprise sales team', 'Review billing FAQ'],
            'contact': ['Submit inquiry form', 'Call direct support line', 'Schedule an in-person meeting'],
            'portfolio': ['Review case study outcomes', 'Schedule project scoping call', 'View client testimonials'],
            'blog': ['Read featured article', 'Sign up for newsletter', 'Share insight on social networks'],
            'faq': ['Find answers without opening ticket', 'Contact support for unresolved inquiries'],
            'booking-search': ['Select travel dates and destination', 'Review flight results', 'Complete booking funnel'],
        }
        return page_goals_map.get(category, ['Explore page content', 'Contact the team', 'Take recommended next step'])

    def _determine_button_text(self, category: str, website_category: str, brief: Dict[str, Any]) -> Tuple[str, str]:
        """Return primary and secondary CTA button copy tailored to the website category."""
        category_buttons = {
            'agriculture': ('Inquire Wholesale', 'Explore Produce'),
            'restaurant': ('Reserve a Table', 'View Tasting Menu'),
            'healthcare': ('Book Appointment', 'Find Specialist'),
            'education': ('Apply for Admission', 'Explore Programs'),
            'ecommerce': ('Shop New Arrivals', 'Browse Best Sellers'),
            'saas': ('Start Free Trial', 'Schedule Live Demo'),
            'portfolio': ('Hire Me', 'View Selected Works'),
            'agency': ('Work With Us', 'Explore Showreel'),
            'blog': ('Subscribe Free', 'Browse Topics'),
            'business': ('Request Consultation', 'View Capabilities')
        }

        if category == 'home' and website_category in category_buttons:
            return category_buttons[website_category]

        buttons_map = {
            'about': ('Our Story', 'Join Our Team'),
            'services': ('Schedule Consultation', 'Explore Services'),
            'service-detail': ('Request Quote', 'View Deliverables'),
            'pricing': ('Select Plan', 'Contact Sales'),
            'contact': ('Send Message', 'Direct Call'),
            'portfolio': ('Start a Project', 'View Case Studies'),
            'blog': ('Subscribe Free', 'Read Insights'),
            'faq': ('Ask a Question', 'Search Knowledgebase'),
            'booking-search': ('Search Flights', 'View Deals'),
        }
        return buttons_map.get(category, ('Get Started', 'Learn More'))

    def plan_page(
        self,
        page: Dict[str, Any],
        page_path: str,
        sitemap_data: Dict[str, Any]
    ) -> PagePlan:
        """
        Generate a comprehensive PagePlan for an individual sitemap page node.
        - Identifies website category & page category
        - Injects industry-tailored blueprints
        - Enforces strict section ordering (navbar first, hero second, footer last)
        - Applies anti-repetition rules & layout diversity
        - Enforces responsive items counts
        """
        if not isinstance(page, dict):
            page = {}

        page_name = str(page.get('name') or 'Page').strip()
        page_id = str(page.get('id') or str(uuid.uuid4())[:8]).strip()
        raw_desc = str(page.get('description') or '').strip()

        brief = sitemap_data.get('brief') if isinstance(sitemap_data, dict) else {}
        if not isinstance(brief, dict):
            brief = {}

        client_name = str(brief.get('client') or '').strip()
        website_category = self.detect_website_category(sitemap_data)
        category = self.detect_page_category(page_name, raw_desc)
        purpose = self._determine_page_purpose(page_name, category, website_category, brief)
        conversion_goals = self._determine_conversion_goals(category, website_category, brief)
        primary_cta, secondary_cta = self._determine_button_text(category, website_category, brief)
        global_nav = self.extract_global_navigation(sitemap_data)

        # Build Section Blueprints
        source_sections = page.get('sections')
        planned_sections: List[PlannedSectionBlueprint] = []

        # Detect whether source_sections is the generic 4-section stub populated by repair_sitemap
        is_generic_stub = False
        if isinstance(source_sections, list) and 0 < len(source_sections) <= 4:
            sec_types = [str(s.get('type') or '').strip().lower() for s in source_sections if isinstance(s, dict)]
            sec_layouts = [str(s.get('layoutVariant') or '').strip().lower() for s in source_sections if isinstance(s, dict)]
            sec_titles = [str(s.get('title') or '').strip().lower() for s in source_sections if isinstance(s, dict)]

            has_framing = 'navbar' in sec_types and 'footer' in sec_types
            all_default_layouts = all(l in ('', 'layout-default', 'default') for l in sec_layouts)
            has_stub_titles = any(t in ('navbar', 'footer', 'key highlights') or 'hero' in t for t in sec_titles)

            if has_framing and all_default_layouts and has_stub_titles:
                is_generic_stub = True

        if isinstance(source_sections, list) and len(source_sections) > 0 and not is_generic_stub:
            # Source sections exist in the sitemap page node: preserve and refine them
            for idx, s in enumerate(source_sections):
                if not isinstance(s, dict):
                    continue
                sec_type = str(s.get('type') or 'content').strip().lower()
                canonical_type = SECTION_TYPE_ALIASES.get(sec_type, sec_type)
                if canonical_type not in SUPPORTED_SECTION_TYPES:
                    canonical_type = 'content'

                title = str(s.get('title') or '').strip()
                if not title:
                    title = f"{page_name} {canonical_type.capitalize()}"

                desc = str(s.get('description') or '').strip()
                layout = str(s.get('layoutVariant') or '').strip().lower()
                layout = LAYOUT_VARIANT_ALIASES.get(layout, layout)
                if layout not in SUPPORTED_LAYOUT_VARIANTS or layout in ('', 'layout-default', 'default'):
                    if canonical_type != 'navbar':
                        canonical_layouts = {
                            'hero': 'layout-split-right',
                            'features': 'layout-grid-3',
                            'services': 'layout-cards',
                            'pricing': 'layout-grid-3',
                            'testimonial': 'layout-cards',
                            'stats': 'layout-grid-4',
                            'team': 'layout-grid-3',
                            'faq': 'layout-list',
                            'cta': 'layout-centered',
                            'gallery': 'layout-grid-3',
                            'process': 'layout-cards',
                            'contact': 'layout-split',
                            'footer': 'layout-multi-column',
                        }
                        layout = canonical_layouts.get(canonical_type, 'layout-split')
                    else:
                        layout = 'layout-default'

                btn_text = str(s.get('buttonText') or '').strip()
                if not btn_text:
                    if canonical_type == 'navbar':
                        btn_text = 'Contact Us'
                    elif canonical_type in ('hero', 'cta'):
                        btn_text = primary_cta
                    elif canonical_type == 'pricing':
                        btn_text = 'Select Plan'

                requires_items = canonical_type in (
                    'features', 'services', 'pricing', 'testimonial', 'stats', 'team', 'faq', 'footer', 'gallery', 'process'
                )

                planned_sections.append(
                    PlannedSectionBlueprint(
                        id=str(s.get('id') or str(uuid.uuid4())[:8]),
                        type=canonical_type,
                        title=title,
                        description=desc,
                        layout_variant=layout,
                        button_text=btn_text,
                        secondary_button_text=secondary_cta if canonical_type in ('hero', 'cta') else '',
                        requires_items=requires_items,
                        items_count=4 if canonical_type in ('footer', 'stats') else 3,
                        order_index=self.SECTION_ORDER_WEIGHTS.get(canonical_type, 50)
                    )
                )
        else:
            # No sections in source page or generic stub: use the category-specific blueprints catalog
            blueprint_tuples = self.get_category_page_blueprint(website_category, category)

            for idx, (stype, stitle, sdesc, slayout, sbtn, ssec_btn) in enumerate(blueprint_tuples):
                title = stitle
                if client_name and '{client}' in title:
                    title = title.replace('{client}', client_name)
                elif stype == 'navbar':
                    title = client_name or 'Brand'
                elif stype == 'hero' and category != 'home':
                    title = f"{page_name} — Overview"

                btn = sbtn or (primary_cta if stype in ('hero', 'cta') else '')
                sec_btn = ssec_btn or (secondary_cta if stype in ('hero', 'cta') else '')

                requires_items = stype in (
                    'features', 'services', 'pricing', 'testimonial', 'stats', 'team', 'faq', 'footer', 'gallery', 'process'
                )

                planned_sections.append(
                    PlannedSectionBlueprint(
                        id=str(uuid.uuid4())[:8],
                        type=stype,
                        title=title,
                        description=sdesc,
                        layout_variant=slayout,
                        button_text=btn,
                        secondary_button_text=sec_btn,
                        requires_items=requires_items,
                        items_count=4 if stype in ('footer', 'stats') else 3,
                        order_index=self.SECTION_ORDER_WEIGHTS.get(stype, 50)
                    )
                )

        # Guarantee Mandatory Framing Sections: Navbar at top, Footer at bottom
        has_nav = any(s.type == 'navbar' for s in planned_sections)
        if not has_nav:
            planned_sections.insert(
                0,
                PlannedSectionBlueprint(
                    id=str(uuid.uuid4())[:8],
                    type='navbar',
                    title=client_name or 'Brand',
                    description='Global navigation header with logo and primary actions.',
                    layout_variant='layout-default',
                    button_text='Contact Us',
                    requires_items=False,
                    order_index=0
                )
            )

        has_footer = any(s.type == 'footer' for s in planned_sections)
        if not has_footer:
            planned_sections.append(
                PlannedSectionBlueprint(
                    id=str(uuid.uuid4())[:8],
                    type='footer',
                    title='Footer',
                    description='Global footer navigation with quick links and company information.',
                    layout_variant='layout-multi-column',
                    button_text='Subscribe',
                    requires_items=True,
                    items_count=4,
                    order_index=100
                )
            )

        # Enforce Section Ordering by Weight
        # Navbar stays first (0), Footer stays last (100), others sort by domain hierarchy
        def sort_key(s: PlannedSectionBlueprint):
            return self.SECTION_ORDER_WEIGHTS.get(s.type, 50)

        planned_sections.sort(key=sort_key)

        # Enforce Anti-Repetition & Layout Alternation
        planned_sections = self.enforce_layout_diversity(planned_sections)

        # Content requirements summary
        content_reqs = [
            f"Highlight {client_name}'s {website_category} offerings and proof points.",
            f"Clear messaging focused on {purpose}.",
            f"Strong primary CTA: '{primary_cta}'.",
            f"Consistent header navigation: {', '.join(global_nav)}."
        ]

        return PagePlan(
            page_name=page_name,
            page_path=page_path or page_name,
            page_id=page_id,
            page_category=category,
            purpose=purpose,
            conversion_goals=conversion_goals,
            primary_cta=primary_cta,
            secondary_cta=secondary_cta,
            content_requirements=content_reqs,
            sections=planned_sections,
            global_navigation=global_nav,
            branding={
                'client': client_name,
                'type': str(brief.get('type') or f'{website_category.title()} Website'),
                'style': str(brief.get('style') or 'Modern, Clean'),
                'tone': str(brief.get('tone') or 'Professional')
            },
            website_category=website_category
        )
