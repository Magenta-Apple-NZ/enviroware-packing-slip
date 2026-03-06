# Enviroware Packing Slip Service

A lightweight Flask webhook that accepts order JSON and returns a formatted PDF packing slip.

---

## Deploy to Railway (recommended)

1. Push this folder to a GitHub repo
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
3. Select your repo — Railway auto-detects the Procfile and deploys
4. Once live, copy your public URL (e.g. `https://your-app.up.railway.app`)

No environment variables needed.

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
| URL | `https://your-app.up.railway.app/packing-slip` |
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
