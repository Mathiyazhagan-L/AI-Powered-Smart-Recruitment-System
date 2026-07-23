import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from core.base import Base

class EmailLog(Base):
    __tablename__ = "email_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=True, index=True)
    email_type = Column(String(100), nullable=False, index=True)
    recipient_email = Column(String(255), nullable=False)
    generated_subject = Column(String(255), nullable=True)
    generated_content_json = Column(Text, nullable=True)
    generated_html = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="Pending", index=True)  # Pending, Sent, Failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)

    # Legacy fields mapping (all nullable Columns in SQLAlchemy mapping to work with DB constraints)
    subject = Column(String(255), nullable=True)
    email_to = Column(String(255), nullable=True)
    event_type = Column(String(100), nullable=True, index=True)
    body = Column(Text, nullable=True)
    delivery_status = Column(String(20), nullable=True)

    @property
    def user_id(self):
        return self.candidate_id

    @user_id.setter
    def user_id(self, value):
        self.candidate_id = value

    def __init__(self, **kwargs):
        # Compatibility mapping for inputs
        user_id_val = kwargs.pop("user_id", None)
        if user_id_val is not None and "candidate_id" not in kwargs:
            kwargs["candidate_id"] = user_id_val
            
        if "email_to" in kwargs and "recipient_email" not in kwargs:
            kwargs["recipient_email"] = kwargs["email_to"]
        if "event_type" in kwargs and "email_type" not in kwargs:
            kwargs["email_type"] = kwargs["event_type"]
        if "body" in kwargs and "generated_html" not in kwargs:
            kwargs["generated_html"] = kwargs["body"]
        if "delivery_status" in kwargs and "status" not in kwargs:
            kwargs["status"] = "Sent" if kwargs["delivery_status"] == "Sent" else "Failed"
            
        super().__init__(**kwargs)
        
        # Populate backward-compatibility fields on insert/init
        if self.recipient_email and not self.email_to:
            self.email_to = self.recipient_email
        if self.email_type and not self.event_type:
            self.event_type = self.email_type
        if self.generated_html and not self.body:
            self.body = self.generated_html
        if self.status and not self.delivery_status:
            self.delivery_status = self.status

        # Supply non-null fallbacks for initial DB insert constraint compliance
        if not self.email_to:
            self.email_to = self.recipient_email or "pending@example.com"
        if not self.event_type:
            self.event_type = self.email_type or "PENDING"
        if not self.subject:
            self.subject = self.generated_subject or "AIHire Notification"
        if not self.body:
            self.body = self.generated_html or "Drafting email..."
        if not self.delivery_status:
            self.delivery_status = self.status or "Pending"
