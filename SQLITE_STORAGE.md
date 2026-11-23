# SQLite Master Storage

SocietyPay uses SQLite for master apartment and resident records:

- `society_settings`
- `apartments`
- `users`

Database file:

`c:\Anand\Aprtmentsw\apartmentsw\societypay.sqlite3`

The following remain in browser `localStorage` (`societyPay.v3`):

- Expenses
- Dues
- Meter bills
- Bill images/PDF attachments
- Payment status and paid dates

## Start the master-data API

```powershell
python societypay_sqlite_api.py
```

It listens on `http://127.0.0.1:4181`.

SocietyPay loads the SQLite master records automatically when `index.html` starts. Flat numbers, resident names, share amounts, society name, billing month, and opening balance are persisted in SQLite.
