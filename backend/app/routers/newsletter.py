from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database.connection import get_db
from database.models import NewsletterEmail
from schemas.newsletter import NewsletterEmailCreate, NewsletterEmailUpdate, NewsletterEmailResponse

router = APIRouter(
    prefix="/api/newsletter",
    tags=["newsletter"]
)

@router.post("/emails", response_model=NewsletterEmailResponse)
def add_email(email_data: NewsletterEmailCreate, db: Session = Depends(get_db)):
    """Adiciona um email à lista da newsletter"""
    # Verifica se email já existe
    existing_email = db.query(NewsletterEmail).filter(NewsletterEmail.email == email_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já está cadastrado na newsletter"
        )

    # Cria novo email
    db_email = NewsletterEmail(
        email=email_data.email,
        name=email_data.name
    )
    db.add(db_email)
    db.commit()
    db.refresh(db_email)

    return db_email

@router.get("/emails", response_model=List[NewsletterEmailResponse])
def list_emails(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista todos os emails da newsletter"""
    emails = db.query(NewsletterEmail).offset(skip).limit(limit).all()
    return emails

@router.get("/emails/active", response_model=List[NewsletterEmailResponse])
def list_active_emails(db: Session = Depends(get_db)):
    """Lista apenas emails ativos da newsletter"""
    emails = db.query(NewsletterEmail).filter(NewsletterEmail.is_active == True).all()
    return emails

@router.put("/emails/{email_id}", response_model=NewsletterEmailResponse)
def update_email(email_id: int, email_data: NewsletterEmailUpdate, db: Session = Depends(get_db)):
    """Atualiza dados de um email da newsletter"""
    db_email = db.query(NewsletterEmail).filter(NewsletterEmail.id == email_id).first()
    if not db_email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email não encontrado"
        )

    # Atualiza campos fornecidos
    update_data = email_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_email, field, value)

    db.commit()
    db.refresh(db_email)
    return db_email

@router.delete("/emails/{email_id}")
def delete_email(email_id: int, db: Session = Depends(get_db)):
    """Remove um email da lista da newsletter"""
    db_email = db.query(NewsletterEmail).filter(NewsletterEmail.id == email_id).first()
    if not db_email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email não encontrado"
        )

    db.delete(db_email)
    db.commit()
    return {"message": "Email removido com sucesso"}

@router.post("/emails/{email_id}/toggle")
def toggle_email_status(email_id: int, db: Session = Depends(get_db)):
    """Ativa/desativa um email da newsletter"""
    db_email = db.query(NewsletterEmail).filter(NewsletterEmail.id == email_id).first()
    if not db_email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email não encontrado"
        )

    db_email.is_active = not db_email.is_active
    db.commit()
    db.refresh(db_email)
    return db_email

