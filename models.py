from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from app import db

# User model for authentication
class User(db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    api_key = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    jobs = relationship('Job', back_populates='user')
    
    def __repr__(self):
        return f'<User {self.username}>'

# Job model for tracking batch processing jobs
class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    vendor_job_id = Column(String(64), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(20), nullable=False, default='processing')  # processing, success, failure, cancelled, queued
    cancelled = Column(Boolean, default=False, nullable=False)  # Flag to indicate if job was cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='jobs')
    deals = relationship('Deal', back_populates='job')
    
    # Indexes
    __table_args__ = (
        Index('idx_job_vendor_job_id', vendor_job_id),
        Index('idx_job_user_status', user_id, status),
    )
    
    def __repr__(self):
        return f'<Job {self.vendor_job_id}>'

# Deal model for individual product IDs in a job
class Deal(db.Model):
    __tablename__ = 'deals'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    deal_id = Column(String(64), nullable=False)
    step_id = Column(String(64), nullable=False)
    priority = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False, default=1)  # 1-processing, 2-success, 3-failure
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    job = relationship('Job', back_populates='deals')
    product = relationship('Product', back_populates='deal', uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_deal_job_id', job_id),
        Index('idx_deal_deal_id', deal_id),
    )
    
    def __repr__(self):
        return f'<Deal {self.deal_id}>'

# Product model for storing product data from Shopee
class Product(db.Model):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    deal_id = Column(Integer, ForeignKey('deals.id'), nullable=False)
    shopee_item_id = Column(String(64), nullable=False)
    raw_data = Column(JSON, nullable=False)  # Store the raw JSON data from Shopee
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    deal = relationship('Deal', back_populates='product')
    
    # Indexes
    __table_args__ = (
        Index('idx_product_shopee_item_id', shopee_item_id),
    )
    
    def __repr__(self):
        return f'<Product {self.shopee_item_id}>'

# Billing model for tracking API usage for billing
class BillingRecord(db.Model):
    __tablename__ = 'billing_records'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    product_count = Column(Integer, nullable=False)  # Number of products processed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User')
    job = relationship('Job')
    
    # Indexes
    __table_args__ = (
        Index('idx_billing_user_id', user_id),
        Index('idx_billing_created_at', created_at),
    )
    
    def __repr__(self):
        return f'<BillingRecord {self.id} - {self.product_count} products>'
