# Enviroware Packing Slip Service

A lightweight Flask app that generates formatted PDF packing slips. Use it two ways:

- **Web form** — open the root URL in a browser, fill in the order details, download the PDF.
- **JSON webhook** — POST order data to `/packing-slip` and get a PDF back (used by Make.com / DocuPipe).

---

## Deploy to Render

1. Push this folder to a GitHub repo
2. Go to [render.com](https://render.com) → **New** → **Web Service** → **Build and deploy from a Git repository**
3. Select your repo — Render auto-detects the `Procfile` (`web: gunicorn app:app ...`) and deploys
4. Once live, copy your public URL (e.g. `https://your-app.onrender.com`)

No environment variables needed. Render will auto-redeploy on every push to `main`.

---

## Web UI

Open the service URL (e.g. `https://your-app.onrender.com/`) in a browser. The form lets you:

- Enter invoice number and PO
- Add / remove ship-to lines
- Add / remove line items (QTY, SKU, description, unit price)
- Click **Generate & Download PDF** — the browser downloads `PKS{invoice_no}.pdf`

Sender details (address, phone, email) are pre-filled with Enviroware defaults but editable per-slip.

---

## API

### `GET /health`
Returns `{"status": "ok"}` — use this to confirm the service is running.

### `POST /packing-slip`
Accepts JSON, returns a PDF file.

**Request body:**
```json
{
  "invoice_no": "00000937",
  "po": "FPON12737696",
  "ship_to": [
    "Farmlands Whakatane",
    "35 Commerce Street",
    "",
    "Whakatane  3120"
  ],
  "company_email": "orders@primetie.co.nz",
  "company_phone": "(07) 549-1716",
  "company_address1": "93 Tetley Road,",
  "company_address2": "Katikati",
  "line_items": [
    ["3", "a pt-b-10", "Prime Tie 10kg Bundled", "$143.00"],
    ["3", "FR 01", "Courier Inner North Island", "$11.00"]
  ]
}
```

- `ship_to` — array of up to 5 strings; empty string `""` adds a small gap
- `line_items` — array of `[qty, sku, description, unit_price]` rows

**Response:** `application/pdf` binary, filename `PKS{invoice_no}.pdf`

---

## Make.com Setup

After your existing DocuPipe webhook step, add these modules:

### Module 1 — HTTP: Make a request
| Field | Value |
|---|---|
| URL | `https://your-app.onrender.com/packing-slip` |
| Method | `POST` |
| Body type | `Raw` |
| Content type | `application/json` |
| Body | *(JSON below — map from DocuPipe output)* |
| Parse response | `No` — we want raw binary |

**Body to map:**
```json
{
  "invoice_no": "{{invoice_no}}",
  "po": "{{po}}",
  "ship_to": [
    "{{ship_to_name}}",
    "{{ship_to_address}}",
    "",
    "{{ship_to_city_postcode}}"
  ],
  "company_email": "orders@primetie.co.nz",
  "company_phone": "(07) 549-1716",
  "company_address1": "93 Tetley Road,",
  "company_address2": "Katikati",
  "line_items": {{line_items}}
}
```

### Module 2 — Google Drive: Upload a file
| Field | Value |
|---|---|
| File name | `PKS{{invoice_no}}.pdf` |
| Data | `{{1.data}}` *(the binary body from the HTTP module)* |
| MIME type | `application/pdf` |
| Folder | Your packing slips folder |

---

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Then test with:
```bash
curl -X POST http://localhost:5000/packing-slip \
  -H "Content-Type: application/json" \
  -d @test_payload.json \
  --output test_output.pdf
```
# enviroware-packing-slip
