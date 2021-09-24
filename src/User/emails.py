from datetime import datetime, timedelta
from fastapi.exceptions import HTTPException
from sqlalchemy.util.langhelpers import counter
from src import crud, schemas
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form
from starlette.responses import JSONResponse
from starlette.requests import Request
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from typing import List
from dotenv import dotenv_values
from src.User.models import User
from src.User import models
from sqlalchemy.orm import Session
import uuid
import jwt


class EmailSchema(BaseModel):
    email: List[EmailStr] = []


class EmailContent(BaseModel):
    message: str
    subject: str


config_credentials = dotenv_values(".env")


conf = ConnectionConfig(
    MAIL_USERNAME=config_credentials["EMAIL"],
    MAIL_PASSWORD=config_credentials["PASS"],
    MAIL_FROM=config_credentials["EMAIL"],
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER="templates/emails",
)


async def send_email(email: List, instance: User, db: Session):
    id = instance.id
    reset_code = str(uuid.uuid1())
    token = reset_code
    db_token = models.Token(
        token_data=token,
        owner_id=id,
        expired_in=datetime.now() + timedelta(minutes=15),
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)

    # token = jwt.encode(token_data, config_credentials["SECRET"], algorithm=["HS256"])

    template = f"""
    <!DOCTYPE html>
        <html>
            <body style="text-align:center;">
                <a href="http://localhost:8000/users/verification/?id={token}">Verify your email</a>
	        </body>
        </html>
            """

    message = MessageSchema(
        subject="email verification",
        recipients=email,
        body=template,
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message=message)
    return JSONResponse(status_code=200, content={"message": "email has been sent"})


async def forgot_password_email(reset_code: str, email: List):
    template = f"""
    <!DOCTYPE HTML>
        <html>
        <body>
        <p>Hi !!!
        <br>Thanks for using fastapi mail, keep using it..!!! A reset code has been sent to you please copy the code and use it to create a new password</p>
        <h1>{reset_code}</h1>
        </body>
        </html>
        """.format(
        email, reset_code
    )

    message = MessageSchema(
        subject="Request for new Password",
        recipients=email,
        body=template,
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message=message)
    return message
