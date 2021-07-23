from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form
from starlette.responses import JSONResponse
from starlette.requests import Request
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from typing import List
from dotenv import dotenv_values
from src.models import User

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
)


async def send_email(email: List, instance: User):
    id = instance.id

    # token = jwt.encode(token_data, config_credentials["SECRET"], algorithm=["HS256"])

    template = f"""
        <html>
        <body>
        <p>Hi !!!
        <br>Thanks for using fastapi mail, keep using it..!!!</p>
        <a href="http://localhost:8000/verification/?id={id}">Verify your email</a>
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
