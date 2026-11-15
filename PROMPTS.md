# Prompts

## Part 1 prompts

### Prompt 1

> Alright I want you to create server using Fast API and the first endpoint is get health endpoint it should return 200 and I want you to right after that to create test script which tests the endpoints themselves in the server and once you create the test script I want you to create a docker file which builds the the or the server and also builds the test as a separate stage OK so and also umm initialize the server with a basic SQLite database so whenever container restarted nothing is persisted Every new container starts with a fresh database, And I want you to consider the coding style mentioned in this markdown file coding-style.md

**Response**

I've built the FastAPI server, the test script and the multi-stage Dockerfile. All 3 tests pass when run locally. I couldn't build the Docker images because Docker Desktop isn't running on your machine, so the Dockerfile itself hasn't been run yet.

**What's there**
- `app/config.py` holds the settings: the database path (`DATABASE_PATH`, which you can override with an environment variable) and the database tables (`SCHEMA_STATEMENTS`). I added one basic `items` table as a starting point.
- `app/database.py` deletes any old database file and creates a new SQLite one each time the server starts.
- `app/main.py` has the server. `GET /health` returns 200 with `{"status": "ok", "database": "ok"}`. It also checks that the database answers.
- `tests/test_endpoints.py` starts the server against its own temporary database and checks three things:
  - `/health` returns 200.
  - The `items` table exists after startup.
  - A row added before a restart is gone after the restart.
- `Dockerfile` has three stages:
  - `base`: Python and the server's packages.
  - `test`: adds pytest and runs the tests during the build, so the build fails if a test fails.
  - `server`: the default stage, which runs the server on port 8000.

**Fresh database on every container:** the database file sits in `/tmp` inside the container with no volume attached, and the server deletes and recreates it at startup. Nothing carries over from one container to the next.

I followed the main rules in `coding-style.md` that apply to code: full-word names, at most three operations per line, settings kept in one place, and small functions with one-line docstrings. Its notebook-only rules (numbered markdown sections, plots) don't apply to a server.

**Once Docker Desktop is running:**
```sh
docker build --target test -t server-test .   # runs the tests during the build
docker build -t server .
docker run --rm -p 8000:8000 server            # then: curl localhost:8000/health
```

---

### Prompt 2

> Alright, so what I wanted to do now is so I'll give you context. So for part one, of this task, is creating two endpoints. One is for registering the members, and the other one is for looking up the members. The members data contains the name, the country, the phone number, as well as the those three. So this is the data model for a member. few checks and verification steps to have in the data model of the member. The name should be trimmed, and minimum is 1 character, maximum is 120 character, and it should be trimmed. For country, there are 3 values allowed only: AE, SA, or BH. Can only be 1 value out of those 3. Now, this is for the data model. This is for the names specifically. All right, so now for the phone number, few things to keep in mind. The structure of the phone number is the following. It should have the plus sign, then the dial code, and then the mobile, or the dial code then the mobile without the plus sign, or a national mobile, a prefix of 00, or a landline, or the wrong length, or anything else yields the status code 422 with the message invalid phone. The entry for the code, as I said, is one value out of the three. AE stands for United Arab Emirates, SA stands for Saudi Arabia, and BH stands for Bahrain. Build the pydantic model of the member off of those three fields.

> *(sent while I was working)* dont build the endpoint yet

**Response**

I built the member model and its tests and left the endpoints out, as you asked. All 27 tests pass, including the 3 earlier endpoint tests.

**The model:** `MemberRegistration` in `app/models.py` has three fields:
- **name:** surrounding spaces are trimmed first, then it must be 1 to 120 characters. Those limits are in `app/config.py`.
- **country:** only `AE`, `SA` or `BH`. Lowercase `ae` or `UAE` are rejected.
- **phone:** only accepted as a plus sign, the dial code, then a mobile number. These all fail with the same error, `invalid phone`:
  - the dial code without the plus
  - a national number like `050…`
  - a `00` prefix
  - a landline
  - the wrong length
  - spaces, letters or an empty value

**Decisions for you to check:**
- **Phone must match the country.** A Saudi mobile on an `AE` member is rejected. You didn't say this outright, but "the dial code" reads as the member's own country's code.
- **Mobile vs landline comes from the `phonenumbers` package.** I added it to `requirements.txt` rather than writing number rules by hand. In its data, Bahrain numbers starting with `66` count as landlines, so they're rejected. If those should be accepted as mobiles, tell me and I'll add an override.
- **The 422 response isn't wired up yet.** The model raises the `invalid phone` error, but turning it into a 422 response with the message `invalid phone` belongs to the endpoint step. By default FastAPI would wrap that message in its own longer error format.

The model tests are in `tests/test_member_model.py`, with a list of valid and invalid numbers you can add to.

---

### Prompt 3

> I said for the phone it could be a plus sign, then dial code, then the mobile number, or dial Additionally, for the structure of the phone, it could be only a national code, then the mobile number. As for checking the phone whether it belongs to the country I'll give you the following conditions So for United Arab Emirates, and Saudi Arabia, the number is 10 digits, and it starts with 05. For Bahrain, it is 8 digits and starts with 3. Without trunk zero.  Additionally, for the structure of the phone, it could be a national number as well. Without the plus sign and without the dial code.

**Response**

The phone check now follows your rules instead of the `phonenumbers` package, and all 38 tests pass. I've removed `phonenumbers` from `requirements.txt`.

**Accepted formats.** Each country's numbers can be written three ways:

| Country | Plus, dial code, mobile | Dial code, mobile | National mobile |
|---|---|---|---|
| AE | `+971501234567` | `971501234567` | `0501234567` (10 digits, starts `05`) |
| SA | `+966551234567` | `966551234567` | `0551234567` (10 digits, starts `05`) |
| BH | `+97336001234` | `97336001234` | `36001234` (8 digits, starts `3`, no trunk zero) |

After the dial code the leading `0` is dropped, so `+9710501234567` is rejected. Everything else fails with `invalid phone`. That covers:
- a `00` prefix
- landlines, meaning any number that doesn't start with `05` (AE, SA) or `3` (BH)
- the wrong length
- a `0` in front of a Bahraini number
- spaces or letters
- a number from another country

**Where the rules live:** each country has its dial code, national prefix and national length in `MEMBER_PHONE_RULES` in `app/config.py`. The model in `app/models.py` builds its checks from those values, so changing a rule or adding a country only means editing that table and the allowed country list in the model.

**Decisions for you to check:**
- **Every number is stored in one format.** Whichever way it's entered, the phone is saved as `+` then the dial code then the number, so `0501234567` becomes `+971501234567`. That way one member can't end up stored under three different spellings, which will matter for lookup. If you'd rather keep the number exactly as entered, it's a one-line change.
- **The phone must belong to the member's country.** A Saudi number on an `AE` member is still rejected.

The endpoints are still not built, as you asked.

---

### Prompt 4

> I want you to avoid building an additional validation or step that is not instructed to you. Only stick to what I give you. Before we move on to the end points I want you to consider the following contract details
>
> **Contract**
> If this does not hold, nothing else can be scored. If your container fails to build or start, you will see that fix required by checking ticket status, and you get 48 hours to push a fix to the same branch.
>
> - A Dockerfile at the repo root. We run docker build -t app . and docker run -p 8080:8080 app. The API listens on 0.0.0.0:8080, and GET /health returns 200 within 60 seconds of start.
> - The same Dockerfile has a stage named test that runs your tests: docker build --target test . must succeed.
> - No network at runtime. Keep state in memory or in an embedded store such as SQLite. Each run starts empty.
> - JSON in and out. Dates are YYYY-MM-DD with no time or timezone.
> - Money is always an integer in minor units (fils, halalas). Every invoice carries its currency.
> - IDs you generate are unique strings in any format.
> - Errors always look like {"error": {"code": "...", "message": "..."}}.
> - Malformed input (a missing field, a wrong type, an unparseable date, a value outside its allowed range) is 422 VALIDATION.
> - An unknown id in the URL is 404 NOT_FOUND.
> - Business errors use the status and code given in each part.
> - Requests can arrive concurrently. Every rule that says something "may not" happen must still hold when two requests race.
>
> we are working on part 1 . So some of the details in the contract will be applicable in other parts. But do take note of the contracts because we will be testing doing automated testing based on the conditions specified in it.

**Response**

I've removed the extra steps and applied the contract rules that already affect the server. All 42 tests pass locally. Docker Desktop still isn't running, so neither Docker build has been tried yet, and the build and start are what the contract checks first.

**Removed (not asked for):**
- **Phone rewriting.** The phone is now stored exactly as entered. The model only checks it against your three formats and the country rules.
- **Database check in `/health`.** It now just returns 200.

**Contract changes:**
- **Port 8080.** The `Dockerfile` now serves on 0.0.0.0:8080. Its default stage is still the server and the `test` stage is unchanged, so `docker build -t app .` and `docker build --target test .` match the contract.
- **Error format.** A new `app/errors.py` returns every error as `{"error": {"code", "message"}}`:
  - Bad input (missing field, wrong type, broken JSON) returns 422 `VALIDATION`, with the first problem as the message. A bad phone gives exactly `{"error": {"code": "VALIDATION", "message": "invalid phone"}}`.
  - Unknown paths return 404 `NOT_FOUND`.
  - Unexpected crashes return 500 `INTERNAL_ERROR`, because the contract says errors always use this format.
- **Tests.** `tests/test_endpoints.py` now checks the 404, the 422 for a missing field, the exact `invalid phone` body and broken JSON. It does this through a dummy route that exists only inside the test, not in the real server.

The placeholder `items` table from the first step is still in `app/config.py`. I plan to replace it with a `members` table when we build the endpoints.

I've saved two notes for future sessions: build only what you specify, and the contract's rules.

To check the Docker side, start Docker Desktop and run:
```sh
docker build --target test .
docker build -t app . && docker run -p 8080:8080 app
```

---

### Prompt 5

> One thing to make sure of the Pydantic model should only do validation. It should not do any sort of correction. So just confirm that the model that you built does not fix anything, rather it flags it only.

**Response (before asking)**

No, not completely. The model changes one thing: it trims the name. `"  Sara  "` is accepted and comes out as `"Sara"`. That's the `strip_whitespace=True` on `MemberName`. I added it because you said the name "should be trimmed", but that's a correction, not a check.

Everything else only flags:
- **Phone:** stored exactly as entered. A number with spaces around it is rejected with `invalid phone`, not cleaned.
- **Country:** must be exactly `AE`, `SA` or `BH`. Lowercase `ae` is rejected, not changed to uppercase.
- **Types:** a number sent where text is expected (`501234567` instead of `"501234567"`) is rejected, not converted.

**Question asked:** The member model currently trims the name, which is a correction. How should it handle a name with spaces at the start or end, like "  Sara  "?
**Answer:** Reject it.

**Response**

The model now only checks and never changes a value. All 47 tests pass.

**What changed:** the name is no longer trimmed. A name with spaces, tabs or newlines at the start or end is rejected with 422 `VALIDATION` and the message `name must not start or end with whitespace`. The 1 to 120 length check is unchanged. A name that's only spaces, like `"   "`, is still rejected, now by the whitespace check.

**Every field now only flags:**
- **name:** must be text, 1 to 120 characters, with no whitespace at either end.
- **country:** must be exactly `AE`, `SA` or `BH`.
- **phone:** must be text in one of your three formats for that country, otherwise `invalid phone`.

Each accepted value comes out exactly as it was sent. The tests in `tests/test_member_model.py` check that, and that each kind of whitespace at the start or end of a name is rejected.

---

### Prompt 6

> Okay, now we can work on the endpoint. The endpoint is where we will make changes to the input itself, right? So whether it's trimming, fixing, removing white space, and so on. Now, the first endpoint, which is the /members post, it's a post endpoint. It receives name, country, and phone. And for the name, it should be trimmed, and the validation obviously comes for the number of characters between 1 and 20, and the country, as I mentioned before, it should be one of those three countries' codes. For the phone number, there's some additional verification. So if a national number is provided, then the endpoint should check the member's own country, which is submitted with it, and the provided national number should fit the country's shape. As for international numbers, the number may be from any of the three countries. Now, one thing to check when the national number is provided, sorry, when the international number is provided, is to match the dial code with the provided country code, and if they are mismatched, then the endpoint should return an error saying phone country mismatch 422. Umm every member can be registered with one phone and no two members can share the same phone in any spelling whether it's  + with a dial code and the mobile or the dial code only and the mobile or the national number and if there's a second write with the same phone number the error that goes back is phone taken 409 with existing member ID inside the error. This must hold when both writes arrive at the same moment.  error message should be in caps like PHONE_TAKEN and PHONE_COUNTRY_MISMATCH

**Response**

`POST /members` is built, and the full suite passes: 69 tests, three runs in a row. Docker still hasn't been tried, since Docker Desktop wasn't running.

**What happens to a request:**
1. **Body check:** `name`, `country` and `phone` must be there and must be text. Anything missing, the wrong type, or broken JSON returns 422 `VALIDATION`.
2. **Endpoint cleans:** it trims the name. That's the only correction.
3. **Model checks:** the model only validates and changes nothing:
   - name is 1 to 120 characters
   - country is `AE`, `SA` or `BH`
   - phone is either a national number in the member's own country's shape, or an international number (with or without `+`) from any of the three countries
   - anything else returns 422 `VALIDATION` with the message `invalid phone`
4. **Country match:** an international number whose dial code belongs to a different country returns 422 `PHONE_COUNTRY_MISMATCH`.
5. **Duplicate phones:** each number is reduced to one spelling, like `+971501234567`, which sits in a database column that can't hold the same value twice. A second member with the same number in any spelling returns:
   ```json
   {"error": {"code": "PHONE_TAKEN", "message": "phone taken", "member_id": "<existing id>"}}
   ```
   Because the database itself enforces this, it still holds when two writes arrive at once. The concurrent test sends 10 requests at the same time using all three spellings. Exactly one is created, and all nine others return `PHONE_TAKEN` with that member's id.
6. **Success:** returns 201 with `{"id", "name", "country", "phone"}`. The id is a generated unique string, and the phone is returned exactly as sent.

The code is in `app/members.py` for the endpoint, `app/phones.py` for the phone shapes, and `app/errors.py` for the new error type. The `items` placeholder table is replaced by `members`.

**Decisions for you to check.** You didn't specify these, so I made a choice for each:
- **Name length:** you said "between 1 and 20" this time, but 120 earlier. I kept 120, assuming a slip. If it's really 20, it's one line in `app/config.py`.
- **Success status:** I used 201 Created, the usual status for creating something.
- **Field name for the existing id:** I put it inside `error` as `member_id`. The automated tests may expect a different name.
- **Message text:** the CAPS values are the error `code`, as the contract's format implies, and the `message` is plain words (`phone taken`, `phone country mismatch`). Tell me if you want the message in caps too.
- **Lookup endpoint:** not built yet, as you only described the POST.

---

### Prompt 7

> then point additionally cleans the phone by removing spaces, hyphens and round brackets. If anything other than digits and one leading + remains, it is 422 INVALID_PHONE.

**Question asked:** After the endpoint strips spaces, hyphens and brackets from the phone, leftover characters return 422 INVALID_PHONE. Today every other phone failure (00 prefix, landline, wrong length, wrong national shape) returns 422 with code VALIDATION and message "invalid phone". Should those use INVALID_PHONE too?
**Answer:** All INVALID_PHONE.

**Response**

The endpoint now removes spaces, hyphens and round brackets from the phone, and every phone failure returns `INVALID_PHONE`. All 85 tests pass.

**What changed:**
- **Cleaning:** before the model checks the phone, the endpoint removes spaces, hyphens, `(` and `)`. So `+971 (50) 123-4567` becomes `+971501234567` and `050-123-4567` becomes `0501234567`. The list of removed characters is `PHONE_CHARACTERS_TO_REMOVE` in `app/config.py`.
- **One error for every bad phone:** each phone failure now returns `{"error": {"code": "INVALID_PHONE", "message": "invalid phone"}}`. That covers leftover characters (dots, letters, tabs, a second `+`, a `+` anywhere but the start), the `00` prefix, landlines, wrong length and the wrong national shape. Other bad input still returns `VALIDATION`. The mapping is in `app/errors.py`.
- **Leftover characters:** I didn't add a separate check, because the existing phone shapes already reject anything other than digits and one leading `+`.
- **Response:** the phone is returned cleaned, since that's what the endpoint passes on and stores.
- **Duplicates:** a cleaned spelling like `+971 (50) 123-4567` counts as the same number as `0501234567`. The duplicate and concurrent tests now include it.

Only the literal space character is removed, as you said "spaces", so a tab returns `INVALID_PHONE`. If tabs and other whitespace should be removed too, it's a one-character change in config.

---

### Prompt 8

> Alright, so now for the get endpoint, which is also /members/lookup, the lookup is through the phone. So when the lookup is done through a national number without a country parameter, the error should be phone needs country 422. If the country is provided, then the national number should fit the country's shape.

**Questions asked and answers:**
- When the phone is valid but no member has it? **404 NOT_FOUND.**
- Should the lookup clean the phone like POST /members does? **Yes, same as POST.**
- Lookup with an international number whose dial code differs from the country parameter? **Ignore country.**
- Lookup with a phone that fits no allowed shape? **422 INVALID_PHONE.**

**Response**

`GET /members/lookup` is built and all 102 tests pass. The stray shell error came from the cleanup step and didn't touch the project. Docker still hasn't been tried.

**How it works:** call it as `GET /members/lookup?phone=...&country=...`, where `country` is optional.
1. **Cleaning:** the phone is cleaned the same way as in `POST /members` (spaces, hyphens and round brackets removed). An unencoded `+`, which arrives as a space, still works.
2. **Checks:** a new lookup model in `app/models.py` only validates:
   - `country` must be `AE`, `SA` or `BH` if it's sent; otherwise 422 `VALIDATION`.
   - An international number is accepted for any of the three countries, and `country` is ignored for it.
   - A national number with `country` must fit that country's shape, otherwise 422 `INVALID_PHONE`.
   - Anything that fits no allowed shape (landline, `00` prefix, wrong length, dots, letters) returns 422 `INVALID_PHONE`.
3. **No country:** a national number sent without `country` returns 422 `PHONE_NEEDS_COUNTRY`.
4. **Result:** 200 with the member `{"id", "name", "country", "phone"}`, found in any spelling (`+971…`, `971…`, `05…` with `country=AE`, or with spaces and brackets). If nobody has that number, it returns 404 `NOT_FOUND`.

**Decisions for you to check:**
- **When `PHONE_NEEDS_COUNTRY` applies:** I treat a number as national without a country only if it fits at least one country's national shape, like `0501234567` or `36001234`. Something like `042345678` fits none of the shapes, so it returns `INVALID_PHONE` rather than asking for a country.
- **Query parameter names:** I used `phone` and `country`, since you didn't name them. If the graders send different names, the requests will fail.
- **Still open from the POST endpoint:** the 120 vs 20 name length, the 201 status, and the `member_id` field name in the `PHONE_TAKEN` error are unconfirmed.

---

### Prompt 9

> **Countries**
>
> | Country | Code | Dial | Currency | Minor units | VAT | National mobile | E.164 mobile |
> |---|---|---|---|---|---|---|---|
> | United Arab Emirates | AE | 971 | AED | 100 fils = 1 AED | 5% | 05X XXX XXXX | +9715XXXXXXXX |
> | Saudi Arabia | SA | 966 | SAR | 100 halalas = 1 SAR | 15% | 05X XXX XXXX | +9665XXXXXXXX |
> | Bahrain | BH | 973 | BHD | 1000 fils = 1 BHD | 10% | 3XXX XXXX | +9733XXXXXXX |
>
> UAE and Saudi national mobiles are 10 digits starting 05. Bahrain national mobiles are 8 digits starting 3, with no trunk zero. Nothing else is a valid phone.
>
> **Part 1. Members and phones**
> Our member table stores the same phone as +966551234567, 966551234567 or 0551234567, depending on which app wrote it, so exact-match lookups miss people. Fix that at the boundary.
>
> POST /members
> `{ "name": "Noura Al Harbi", "country": "SA", "phone": "055 123 4567" }`
> → 201 `{ "id": "…", "name": "Noura Al Harbi", "country": "SA", "phone": "+966551234567" }`
>
> GET /members/lookup?phone=966551234567
> GET /members/lookup?phone=%2B966551234567
> GET /members/lookup?phone=055%20123%204567&country=SA
> → 200 the same member each time. 404 NOT_FOUND if nobody has that number.
> name is trimmed, then must be 1 to 120 characters, and is returned trimmed. country is AE, SA or BH.
>
> Clean. Remove spaces, hyphens and round brackets. If anything other than digits and one leading + remains, it is 422 INVALID_PHONE.
> Three spellings. What remains must be + then dial code then mobile, or dial code then mobile without the +, or a national mobile. A 00 prefix, a landline, a wrong length, or anything else is 422 INVALID_PHONE.
> National numbers need a country.
> On POST /members, a national number is read in the member's own country and must fit that country's shape.
> On lookup, a number that fits any country's national shape with no country parameter is 422 PHONE_NEEDS_COUNTRY. With a country, it must fit that country's shape.
> International numbers.
> On lookup, a country parameter that disagrees with the dial code is 422 PHONE_COUNTRY_MISMATCH.
> On POST /members, the number may be from any of the three countries, since members carry foreign SIMs.
> One member per phone. Two members may not share a phone in any spelling. The second write gets 409 PHONE_TAKEN, with existing_member_id inside error. This must hold when both writes arrive at the same moment.
>
> this is the part 1 content, is there anything missed before moving on to part 2?

**Response (before fixing)**

Comparing the spec with what's built, I found four gaps. Three of them come from guesses I made earlier that the spec now answers:

1. **POST must return the phone in one standard form.** `"055 123 4567"` must come back as `"+966551234567"`. We currently return the cleaned number as sent (`0551234567`).
2. **No country mismatch on POST.** The spec says a member's number "may be from any of the three countries, since members carry foreign SIMs". We currently reject those with `PHONE_COUNTRY_MISMATCH`.
3. **Country mismatch belongs to lookup.** If the `country` parameter disagrees with the dial code, lookup must return 422 `PHONE_COUNTRY_MISMATCH`. We currently ignore the country.
4. **Field name in the `PHONE_TAKEN` error.** It must be `existing_member_id`, not `member_id`.

Everything else matches the spec: the name rules, the cleaning, the three spellings, `INVALID_PHONE`, `PHONE_NEEDS_COUNTRY`, 404 `NOT_FOUND`, and duplicates blocked even when two writes arrive at once. Since the stored phone will now always be in the standard form, the separate `canonical_phone` column is no longer needed, and the phone column itself can block duplicates.

**Response**

Yes, four things were missing. They're now fixed and all 110 tests pass, including the spec's own examples copied exactly as written.

**What was fixed:**
1. **POST returns the phone in one standard form.** `"055 123 4567"` with `SA` now comes back as `"+966551234567"`. That form is what's stored, so the lookup returns it too.
2. **Foreign SIMs are accepted on POST.** An `AE` member with `+966551234567` is now registered. Before, it was wrongly rejected with `PHONE_COUNTRY_MISMATCH`.
3. **Country mismatch is now checked on lookup.** If the `country` parameter disagrees with the dial code, lookup returns 422 `PHONE_COUNTRY_MISMATCH`. This replaces the "ignore country" answer you gave me earlier, because the spec says otherwise.
4. **`PHONE_TAKEN` uses `existing_member_id` inside `error`.**

Because the stored phone is always in the standard form, I dropped the extra `canonical_phone` column. The `phone` column now refuses duplicates itself, which still blocks two writes of the same number arriving at once.

**Confirmed against the spec:**
- 201 on create
- the name trimmed, 1 to 120 characters, returned trimmed
- the cleaning, three spellings and `INVALID_PHONE` rules
- `PHONE_NEEDS_COUNTRY` only for numbers that fit some country's national shape
- 404 `NOT_FOUND`
- the three lookup URLs from the spec (`966551234567`, `%2B966551234567`, `055%20123%204567&country=SA`) all return the same member

**Not checked yet: the Docker build.** Docker Desktop is still off, so neither `docker build -t app .` nor `docker build --target test .` has been run. The contract says nothing is scored if the container fails to build or start, so please start Docker Desktop and let me run both before you push. The currencies and VAT rates in the table are for later parts, so I haven't added them yet.

---

### Prompt 10

> I wanted to restructure the app folder a bit so I have the script file as it is and I want you to create a subfolder called endpoints. And have the members script in it. And then have another folder called helpers. Which includes the config, the database, the errors, the models, and the phones. Scripts. For the models, I have a separate folder called models. And inside this models folder, move the models script into it. And rename the script into member. .py.

**Response**

I've moved the files and updated every import. All 110 tests still pass.

```
app/
├── main.py
├── endpoints/
│   └── members.py
└── helpers/
    ├── config.py
    ├── database.py
    ├── errors.py
    ├── phones.py
    └── models/
        └── member.py      (was models.py)
```

Each new folder also has an empty `__init__.py`, which Python needs to import from it. The Dockerfile needed no changes: it copies the whole `app` folder, and the server is still started from `app.main`. As I said at the start, I put `models/` inside `helpers/`; tell me if it should sit directly under `app/` instead.

---

### Prompt 11

> move the models folder outside of the helpers.

**Response**

I've moved the `models` folder out of `helpers`, so the model file is now `app/models/member.py`. I updated the two files that import from it, and all 110 tests still pass.

```
app/
├── main.py
├── endpoints/members.py
├── helpers/  (config, database, errors, phones)
└── models/member.py
```

---

### Prompt 12

> I forgot one thing in the Member model there should be the ID as well It's a field not when registering but when looking up

**Response**

I've added the `id` field. It's in a new `Member` model, and the lookup now returns it. All 110 tests still pass.

- **The model:** `Member` in `app/models/member.py` takes all the registration fields (name, country, phone, with the same checks) and adds `id: str`. The registration model itself still has no `id`, so it isn't part of what's sent to register.
- **The lookup:** `app/endpoints/members.py` builds a `Member` from the stored row and returns it. The response body is unchanged: `id`, `name`, `country`, `phone`.

`POST /members` also returns an id, but it still builds its response as a plain dictionary. Since you said lookup only, I didn't switch it to `Member`; it's a one-line change if you want both to use it.

---

### Prompt 13

> The ID should be The ID should be a base 62 created one registry, and then that gets registered in the database, right? So when registering, the ID should be auto-generated with the encoding base 62.

**Response**

Member ids are now generated in base62 when someone registers. All 111 tests pass, including a new one that checks registered ids use only base62 characters.

- **How the id is made:** registration creates a random 128-bit number (a UUID) and writes it in base62, using `0-9`, `A-Z` and `a-z`. Ids look like `65wQZ2fUGsmfLCzUqzN4pu`. The id is stored in the database, and the lookup returns that same stored id.
- **Where it lives:** the encoder is in `app/helpers/ids.py`, and the character set is `BASE62_ALPHABET` in `app/helpers/config.py`.
- **Length:** ids are usually 22 characters, and once in a while 21, because I didn't pad them to a fixed length.

---

### Prompt 14

> All right, let's start with part 2. I'll give you the first section of part 2, to create the Pydantic model for the plans. And for the agreements, but before that I wanted to create another Pydantic model, a data model for the countries. Based on the table that I gave you, to store the country name, the code, the dial, the currency, the minor units, the VAT, the national mobile, structure, and the international one structure. Once you create the data model for the country, I want you to apply that data model in the phone validation. That we already wrote. Once you do that, then inform me so that we can start with part 2.
>
> **Part 2. Plans and the invoice schedule**
> We create plans through the API; do not seed any.
>
> POST /plans
> `{ "id": "anytime-sa", "country": "SA", "monthly": 29900, "joining_fee": 0 }`
> → 201 `{ "id": "anytime-sa", "country": "SA", "currency": "SAR", "monthly": 29900, "joining_fee": 0 }`
> id is chosen by the caller, and a duplicate is 409 PLAN_EXISTS. monthly is an integer above 0 and joining_fee is an integer of 0 or more, both before VAT, in minor units. Currency and VAT rate come from the country.
>
> POST /agreements
> `{ "member_id": "…", "plan_id": "anytime-sa", "start_date": "2026-09-20", "due_day": 1 }`
> → 201 `{ "id": "…", "member_id": "…", "plan_id": "anytime-sa", "start_date": "2026-09-20", "due_day": 1 }`
> due_day is 1 to 31. A member may hold several agreements.
> An unknown member is 422 UNKNOWN_MEMBER, and an unknown plan is 422 UNKNOWN_PLAN.
> A plan from a different country than the member is 422 PLAN_COUNTRY_MISMATCH.

**Response**

The country model is built and the phone checks now read from it. All 111 existing tests pass unchanged, so phone behaviour is the same as before.

- **The model:** `Country` in `app/models/country.py` has `name`, `code`, `dial_code`, `currency`, `minor_unit`, `minor_units_per_unit`, `vat_percent`, `national_mobile` and `e164_mobile`. It only checks types, with no extra rules.
- **The data:** your table is in `app/helpers/config.py` as `COUNTRY_TABLE`, and `app/helpers/countries.py` loads it into one `Country` per code.
- **Phone checks:** they now work directly from the table's mobile masks, such as `05X XXX XXXX` and `+9715XXXXXXXX`. `X` is any digit and spaces are ignored.
  - The fixed part of a mask sets how a number must start, and the number of `X`s sets the length.
  - The same mask without its `+` covers the dial-code-only spelling.
  - To convert a number to the stored form, its free digits go into the `+9715XXXXXXXX` mask.
- **Removed:** the old rules (`MEMBER_PHONE_RULES` and the trunk-zero setting) are gone, since the masks already contain that information.

How I stored two of the columns:
- **Minor units:** "100 fils = 1 AED" is split into `minor_unit: "fils"` and `minor_units_per_unit: 100`.
- **VAT:** stored as a whole-number percent (`vat_percent: 5`), so invoice maths can stay in integers.

The member model still lists the allowed countries `AE`, `SA`, `BH` by hand, separately from the table. I left it since you only asked for the phone checks to use the new model. Making it read the codes from `COUNTRIES` is a small change if you want it.

Ready for Part 2: send the plan and agreement model details whenever you are.

---

### Prompt 15

> Do add the change for the countries as well.

**Response**

The member model now takes its list of allowed countries from the countries table instead of listing `AE`, `SA`, `BH` by hand. All 111 tests pass.

In `app/models/member.py`, `MemberCountry` is built from the codes in `COUNTRIES`. The table in `app/helpers/config.py` is now the only place countries are defined, so a new row there is allowed for members and gets its phone shapes automatically. Behaviour is unchanged: an unknown country still returns 422 `VALIDATION` with `Input should be 'AE', 'SA' or 'BH'`.

Ready for Part 2.

---

### Prompt 16

> Before we proceed, I want you to put the assumptions that we have made so far in bullet points in and create sections out of these assumptions, and put them in note put them in notes.md. and structure it this way: put part 1 assumptions, and then part 2 assumptions, and then part 3 assumptions.

**Response**

I've written the assumptions into `notes.md` as bullet points, with a section for each part.

- **Part 1:** grouped under server and contract, models vs endpoints, ids, `POST /members` and `GET /members/lookup`.
- **Part 2:** so far only the country model choices, such as how minor units, VAT and the mobile masks are stored.
- **Part 3:** a placeholder for now.

I'll add to it as we go. Ready for Part 2 when you are.

---

### Prompt 17

> I want you to dump the current conversation that we've had into a markdown file called prompts, and create a section inside it called part 1 prompts, and in it have my prompt and your response. The entire conversation till now, and we will do the same for the other parts.

**Response**

Written to `prompts.md` (this file).

---

## Part 2 prompts

### Prompt 1

> **Part 2. Plans and the invoice schedule**
> We create plans through the API; do not seed any.
>
> POST /plans
> `{ "id": "anytime-sa", "country": "SA", "monthly": 29900, "joining_fee": 0 }`
> → 201 `{ "id": "anytime-sa", "country": "SA", "currency": "SAR", "monthly": 29900, "joining_fee": 0 }`
> id is chosen by the caller, and a duplicate is 409 PLAN_EXISTS. monthly is an integer above 0 and joining_fee is an integer of 0 or more, both before VAT, in minor units. Currency and VAT rate come from the country.
>
> POST /agreements
> `{ "member_id": "…", "plan_id": "anytime-sa", "start_date": "2026-09-20", "due_day": 1 }`
> → 201 `{ "id": "…", "member_id": "…", "plan_id": "anytime-sa", "start_date": "2026-09-20", "due_day": 1 }`
> due_day is 1 to 31. A member may hold several agreements.
> An unknown member is 422 UNKNOWN_MEMBER, and an unknown plan is 422 UNKNOWN_PLAN.
> A plan from a different country than the member is 422 PLAN_COUNTRY_MISMATCH.
>
> GET /agreements/{id}/invoices?from=2026-09-01&to=2026-12-31
> → 200
> ```
> [
>   { "invoice_no": 1, "due_date": "2026-09-20", "kind": "FIRST",
>     "proration": { "days": 11, "cycle_days": 30 },
>     "net": 10963, "vat": 1644, "total": 12607, "currency": "SAR" },
>   { "invoice_no": 2, "due_date": "2026-10-01", "kind": "MONTHLY", "proration": null,
>     "net": 29900, "vat": 4485, "total": 34385, "currency": "SAR" },
>   …
> ]
> ```
> Agreements never end. Invoices are computed on request, so there is nothing to store.
> from and to are required and inclusive, and filter on due_date.
> to before from, or more than 366 days after it, is 422 INVALID_RANGE.
> invoice_no is the invoice's position in the agreement's whole schedule. It does not restart inside the range.
>
> **Rules**
>
> Due dates. An agreement's due date in a month is min(due_day, days in that month). Due on the 31st means 30 April, 28 February (29th in a leap year) and 31 March. The anchor stays 31; only the date clamps.
>
> First invoice. Invoice 1 has kind FIRST and is due on the start date. Let N be the first due date strictly after the start date, and P the due date one month before N.
>
> Its net is monthly × (N − start) / (N − P), rounded, plus joining_fee.
> Its proration is {days: N − start, cycle_days: N − P}.
> A start date that is itself a due date gives days = cycle_days, which is the full price.
>
> Later invoices. Invoice 2 has kind MONTHLY, the full monthly price, and is due on N. Invoice 3 is due on the next month's due date, and so on. proration is null.
>
> Rounding. Round half up to a whole minor unit, exactly twice per invoice and never in between:
> - once for the prorated amount;
> - once for vat = net × VAT rate.
>
> total = net + vat. The joining fee sits inside the VAT base.
>
> Minor units only. Never round in major units. A BHD VAT of 579 fils is 0.579 BHD; rounding it to 0.58 is wrong.
>
> Worked examples.
>
> Start 20 Sep 2026, due day 1, SA plan above. N = 1 Oct and P = 1 Sep, so 11/30.
> 29900 × 11 / 30 = 10963.33, which rounds to a net of 10963.
> VAT is 1644.45, which rounds to 1644. The total is 12607.
>
> Start 5 Sep 2026, due day 20, AE plan with monthly 24900 and joining fee 9900. N = 20 Sep and P = 20 Aug, so 15/31.
> 24900 × 15 / 31 = 12048.39, which rounds to 12048. Adding the joining fee gives a net of 21948.
> VAT is 1097.4, which rounds to 1097. The total is 23045.
> Invoice 2 is due 20 Sep, so September has two invoices.
>
> Before doing anything I want to note down the assumptions the for this part part two the first assumption is invoices must be stored because each invoice is unique and they cannot computed on the fly

**Response**

I've added it to the Part 2 section of `notes.md`:

> - Invoices must be stored, because each invoice is unique and cannot be computed on the fly.

This goes against one line of the spec: "Invoices are computed on request, so there is nothing to store." The graders' tests check what the API returns, so storing is fine as long as every request still returns exactly the computed schedule. Three things need care:
- **No end date:** agreements never end, so there's no fixed set of invoices to store up front. The `from`/`to` range can reach any date.
- **Clashing stores:** two requests for the same range arriving at once must not save the same invoice twice.
- **Matching the computed schedule:** a stored invoice must match what the rules would compute. If it doesn't, the graders' checks fail.

A common middle ground: compute each invoice from the rules, and save it the first time it's returned, keyed by agreement and `invoice_no`, so later requests return the same saved record. If that's what you mean by storing, I'll build it that way when we get to the invoices endpoint. Nothing has been built yet. Send the next assumption, or tell me to start.

### Prompt 2

> Okay, before we build the endpoints, let's build the data models. So before you even write it, as a code, I want you to draft the data model, or at least the fields for each data model. So the first one is the plans, second one is agreements, third is invoices. Show me the data models. First,

**Response**

Here's a draft of the fields for each model. No code yet. I've followed the same pattern as members: a request model that only checks the request body's fields and types, then a model that validates the values, then the stored model with any generated fields.

**1. Plans**

`PlanCreation`: the `POST /plans` body.

| Field | Type | Rule |
|---|---|---|
| `id` | string | Chosen by the caller |
| `country` | `AE` / `SA` / `BH` | Taken from the countries table, like members |
| `monthly` | integer | > 0, minor units, before VAT |
| `joining_fee` | integer | ≥ 0, minor units, before VAT |

`Plan`: stored and returned. All of the above, plus `currency` (string), taken from the country (`SA` → `SAR`).

The VAT rate isn't a field. It's read from the country when invoices are computed, because the spec's response doesn't include it.

**2. Agreements**

`AgreementCreation`: the `POST /agreements` body.

| Field | Type | Rule |
|---|---|---|
| `member_id` | string | Must exist, otherwise `UNKNOWN_MEMBER` (checked by the endpoint) |
| `plan_id` | string | Must exist, otherwise `UNKNOWN_PLAN` (checked by the endpoint) |
| `start_date` | date | `YYYY-MM-DD` only |
| `due_day` | integer | 1 to 31 |

`Agreement`: stored and returned. All of the above, plus `id` (string), generated in base62 like member ids.

`PLAN_COUNTRY_MISMATCH` (plan country ≠ member country) is checked by the endpoint, because it needs both records from the database.

**3. Invoices**

`InvoiceRange`: the query of `GET /agreements/{id}/invoices`. `from` and `to` are required `YYYY-MM-DD` dates, both inclusive. `to` before `from`, or more than 366 days after it, is 422 `INVALID_RANGE`.

`Proration`: `days` (integer, N − start) and `cycle_days` (integer, N − P).

`Invoice`: stored, per your assumption, and returned.

| Field | Type | Rule |
|---|---|---|
| `agreement_id` | string | Stored only, not in the response |
| `invoice_no` | integer | Position in the whole schedule, starting at 1 |
| `due_date` | date | `YYYY-MM-DD` |
| `kind` | `FIRST` / `MONTHLY` | `FIRST` only for invoice 1 |
| `proration` | `Proration` or null | Only on `FIRST`, null on `MONTHLY` |
| `net` | integer | Minor units |
| `vat` | integer | Minor units |
| `total` | integer | `net + vat` |
| `currency` | string | Taken from the plan |

In storage, `agreement_id` + `invoice_no` is unique, so the same invoice can't be saved twice even when two requests arrive at once.

**Decisions for you**
1. **Strict types:** the contract makes a wrong type 422 `VALIDATION`, so I plan to reject `"29900"` (a string), `29900.0` (a decimal) and `true` (a yes/no value) for `monthly`, `joining_fee` and `due_day`, rather than converting them. Agree?
2. **Strict dates:** only exactly `YYYY-MM-DD` is accepted. Pydantic would otherwise also accept forms like `2026-09-20T00:00:00` or a raw number.
3. **Plan `id`:** the spec only says the caller chooses it. I'll accept any text, with no format rules, unless you want limits such as no empty string.

Once you confirm or adjust these, I'll write the models.

### Prompt 3

> For the strict type, correct. Validate only as integer. For the strict dates and the plan, decision, go ahead with them.

**Response**

The three sets of models are written, and all 151 tests pass (111 existing plus 40 new model tests).

**New files:**
- `app/models/plan.py`: `PlanCreation` (`id`, `country`, `monthly` > 0, `joining_fee` ≥ 0) and `Plan` (adds `currency`).
- `app/models/agreement.py`: `AgreementCreation` (`member_id`, `plan_id`, `start_date`, `due_day` 1 to 31) and `Agreement` (adds `id`).
- `app/models/invoice.py`:
  - `InvoiceRange`: `from` and `to`. Inside the code they're `from_date` and `to_date`, because `from` is reserved in Python, but the query still uses `from` and `to`.
  - `Proration`
  - `Invoice`: its stored `agreement_id` is left out of the response.
- `app/models/types.py`: two shared field types:
  - `StrictInteger`: whole numbers only, so `"29900"`, `29900.0` and `true` are rejected.
  - `IsoDate`: exactly `YYYY-MM-DD`, so forms with a time, unpadded dates like `2026-9-20`, impossible dates like `2026-02-30`, and raw numbers are rejected.

**Supporting changes:**
- **Shared country type:** the allowed-country type (`CountryCode`) now lives in `app/helpers/countries.py`, so members and plans share one list taken from the countries table.
- **New settings:** `DUE_DAY_MIN`, `DUE_DAY_MAX` and `MAX_INVOICE_RANGE_DAYS = 366` are in `app/helpers/config.py`.
- **Range errors:** a bad range is flagged by the model and returned as 422 `INVALID_RANGE`, the same way `INVALID_PHONE` works. Missing or malformed `from`/`to` stays `VALIDATION`.

**Why dates need their own type:** Pydantic's built-in strict mode accepts only `YYYY-MM-DD` in JSON bodies, but it rejects all plain text, and `from`/`to` arrive as query-string text. `IsoDate` checks the exact shape itself, so it works for both.

**Still open:**
- **Not checked by the models:** the business checks (`UNKNOWN_MEMBER`, `UNKNOWN_PLAN`, `PLAN_COUNTRY_MISMATCH`, `PLAN_EXISTS`) need the database, so they'll be in the endpoints.
- **Invoice fields:** `Invoice` only checks field types, without cross-checks like `total = net + vat`, since those values will be computed by the endpoint's own rules.
- **Nothing built beyond the models yet:** no endpoints, no database tables.

### Prompt 4

> Alright, now for the endpoints. Implement the post endpoint for plans. And for agreements.

**Response**

`POST /plans` and `POST /agreements` are built, and all 183 tests pass (151 before, plus 32 new endpoint tests).

**POST /plans** (`app/endpoints/plans.py`)
- **Body check:** the `PlanCreation` model checks the body. Bad values return 422 `VALIDATION`, for example a missing field, an unknown country, `monthly` ≤ 0, `joining_fee` < 0, or a non-integer such as `"29900"`, `29900.0` or `true`.
- **Currency:** taken from the country (`SA` → `SAR`).
- **Response:** 201 with exactly the spec's shape: `{"id", "country", "currency", "monthly", "joining_fee"}`.
- **Duplicate id:** 409 `PLAN_EXISTS`. The plan id is the table's primary key, so this also holds when two writes arrive at once. A test sends 10 at the same time and gets one 201 and nine 409s.
- **No seeding:** no plans are created at startup.

**POST /agreements** (`app/endpoints/agreements.py`)
- **Body check:** the `AgreementCreation` model checks the body. A malformed `due_day` (outside 1 to 31, or not an integer) or a malformed `start_date` (not exactly `YYYY-MM-DD`, or an impossible date) returns 422 `VALIDATION`.
- **Business checks, in the spec's order:**
  1. unknown member: 422 `UNKNOWN_MEMBER`
  2. unknown plan: 422 `UNKNOWN_PLAN`
  3. plan country different from the member's country: 422 `PLAN_COUNTRY_MISMATCH`
- **Response:** 201 with `{"id", "member_id", "plan_id", "start_date", "due_day"}`. The id is generated in base62, and `start_date` is returned as `YYYY-MM-DD`.
- **Several agreements:** a member may hold several, as the spec allows.

**Supporting changes:**
- **New tables:** `plans` and `agreements`, in the database schema in `app/helpers/config.py`.
- **Shared database code:** `app/helpers/database.py` now has one function for writes and one for single-row reads. The member, plan and agreement queries all use them.
- **Shared test setup:** the test server setup and body builders moved to `tests/conftest.py`, so the member tests and the new `tests/test_plans_and_agreements.py` share them.

**Decisions for you to check:**
- **The member's country** is the one checked against the plan, not the country of the member's phone. So an `AE` member with a Saudi SIM can't take an `SA` plan.
- **Messages** follow the same style as Part 1: `plan exists`, `unknown member`, `unknown plan`, `plan country mismatch`.

The invoices endpoint isn't built yet.

### Prompt 5

> add an exception for the agreement if a second agreement request attempts to use the same plan ID with the member ID, it rejects and returns 409 AGREEMENT_EXISTS.

**Response**

A second agreement for the same member and plan is now rejected with 409 `AGREEMENT_EXISTS`. All 186 tests pass, two runs in a row.

- **How:** the `agreements` table makes the pair member + plan unique. The endpoint turns the database's refusal into `{"error": {"code": "AGREEMENT_EXISTS", "message": "agreement exists"}}`. Because the database enforces it, it holds when two requests arrive at once. A test sends 10 at the same time and gets one 201 and nine 409s.
- **Order of checks:** `UNKNOWN_MEMBER`, `UNKNOWN_PLAN` and `PLAN_COUNTRY_MISMATCH` are still checked first. `AGREEMENT_EXISTS` comes last, when the agreement is saved.
- **Only member + plan counts:** a different `start_date` or `due_day` doesn't make it a new agreement.
- **Still allowed:**
  - a member holding several agreements on different plans (the spec's "a member may hold several agreements")
  - two members on the same plan
- **Tests:** in `tests/test_plans_and_agreements.py`. The earlier "several agreements" test used the same plan twice, so it now uses two different plans.

I haven't added this to `notes.md`, since you didn't ask me to note it. Tell me if you want it there.

### Prompt 6

> Once an agreement is created, and response for that endpoint is returned, immediately start a background task and create 6 dummy invoices. And follow the invoice creation rules mentioned. In the part and once you build that, then build the get request endpoint for the agreements first, the agreements prefix along with the ID after, and the response for that is the details or the fields of the agreement, all of it, and when it is again when invoices is request a specifically of the agreements, it should return them in the same format that is mentioned in the part.

**Response**

All three pieces are built, and all 206 tests pass (186 before, plus 20 new invoice tests), two runs in a row.

**1. Background invoices on agreement creation**
- **When:** right after `POST /agreements` sends its 201, a background task stores the agreement's first 6 invoices, following the spec's rules. The count is `INITIAL_INVOICE_COUNT` in `app/helpers/config.py`.
- **The rules,** in `app/helpers/invoices.py`:
  - **Due dates:** min(due_day, days in month). Day 31 clamps to 30 Apr and to 28 or 29 Feb, and the anchor stays 31.
  - **Invoice 1:** `FIRST`, due on the start date. Its net is monthly × (N − start) / (N − P), rounded, plus the joining fee, with `proration {days, cycle_days}`.
  - **Invoices 2 onward:** `MONTHLY`, due on N and then one month after another, at the full monthly price, with `proration: null`.
  - **Rounding:** half up to a whole minor unit, exactly twice: once for the prorated amount and once for the VAT. It uses whole numbers only, never major units. `total = net + vat`, and the joining fee is inside the VAT base.
- **Storage:** a new `invoices` table keyed by agreement + `invoice_no`.

**2. GET /agreements/{id}**
- Returns 200 with all the agreement's fields (`id`, `member_id`, `plan_id`, `start_date`, `due_day`), the same as the POST response.
- An unknown id returns 404 `NOT_FOUND`.

**3. GET /agreements/{id}/invoices?from=…&to=…**
- **Response:** 200 with a list in the spec's exact format: `invoice_no`, `due_date`, `kind`, `proration`, `net`, `vat`, `total`, `currency`. The stored `agreement_id` is left out.
- **Range:** `from` and `to` are required and inclusive, and filter on `due_date`.
  - `to` before `from`, or more than 366 days after it: 422 `INVALID_RANGE`.
  - Missing or malformed dates: 422 `VALIDATION`.
  - Unknown agreement: 404 `NOT_FOUND`.
- **Numbering:** `invoice_no` is the position in the whole schedule. A range in 2027 starts at invoice 5 or later, not at 1.
- **Past the first 6:** agreements never end, so when a range asks for an invoice that isn't stored yet, the endpoint computes it with the same rules and stores it. The response is then read back from storage. Saving skips invoices already stored, so requests that arrive at once never store one twice. A test sends 10 at the same time and finds each of the 16 invoices stored once.

**Checked against the spec:**
- **Worked example 1** (SA, start 20 Sep 2026, due day 1): invoice 1 is `{days: 11, cycle_days: 30}`, net 10963, VAT 1644, total 12607. Invoice 2 is due 1 Oct: 29900 + 4485 = 34385. Both match the spec's exact bodies.
- **Worked example 2** (AE, 24900 + 9900 joining fee, start 5 Sep, due day 20): `{15, 31}`, net 21948, VAT 1097, total 23045, and two invoices in September.
- **Also covered:** due day 31 across a leap February, a start on a due date charging full price, Bahraini VAT of 579 fils staying in fils, and a VAT of exactly 0.5 rounding up to 1.

**Decisions for you to check:**
- **"Dummy" invoices:** I took this to mean the first 6 real invoices of the schedule, computed by the rules, not placeholder values.
- **Invoices outside the first 6** are computed and stored the first time a range asks for them, as described above. Without this, a range past the 6th invoice would come back short.
- **Check order on the invoices endpoint:** the range is checked before the agreement is looked up. So a bad range on an unknown agreement returns 422, not 404.

### Prompt 7

> Change the invoice storage approach to just computed invoices. Don't store any invoice.

**Response**

Invoices are now only computed, never stored. All 206 tests pass, two runs in a row, and nothing related to storing invoices is left in the code.

**Removed:**
- the `invoices` table and the `INITIAL_INVOICE_COUNT` setting (`app/helpers/config.py`)
- the background task that stored 6 invoices after `POST /agreements`
- the database functions for saving and reading invoices (`app/helpers/database.py`)
- the code that converted invoices to and from database rows, and the first-6-invoices builder (`app/helpers/invoices.py`)
- the `agreement_id` field on the `Invoice` model, which only existed for storage

**How it works now:**
- **Invoices endpoint:** `GET /agreements/{id}/invoices` checks the range, looks up the agreement and its plan, computes the invoices due in the range from the rules, and returns them. The response format is unchanged.
- **Agreement creation:** `POST /agreements` just saves and returns the agreement.
- **Unchanged:** `GET /agreements/{id}`.

**Tests:**
- The background-storage test is replaced by one that checks no `invoices` table exists, even after invoices are requested.
- The concurrent-requests test now checks that 10 requests at once all get the same schedule.
- All the spec's examples and edge cases still pass with the same numbers.

`notes.md` still has your earlier Part 2 assumption, "Invoices must be stored, because each invoice is unique and cannot be computed on the fly". That now contradicts the code. Should I remove it or replace it?

### Prompt 8

> Since there's a range now, for the invoices, update the agreements get endpoint to not return the invoices, but rather only the fields that are registered, which are the agreement ID, obviously, and the member ID, the plan ID, the start date, and the due date.

**Response**

No change was needed. `GET /agreements/{id}` already returns only the agreement's stored fields and no invoices. I checked by calling it:

```json
{
  "member_id": "3v2NaLTAjlRpgHHm6ReEM",
  "plan_id": "anytime-sa",
  "start_date": "2026-09-20",
  "due_day": 1,
  "id": "2W44DRpnd6YTk16tHuWIZk"
}
```

- **Fields:** `id`, `member_id`, `plan_id`, `start_date` and `due_day`. That's the due *day* (1 to 31), which is what's stored, since due dates are only worked out when invoices are computed.
- **Invoices:** only returned by `GET /agreements/{id}/invoices?from=…&to=…`. That was already true before this change, because the 6 background invoices were stored but never returned by this endpoint.
- **Test:** `test_get_agreement_returns_all_fields` in `tests/test_invoices.py` checks the response equals the POST response exactly, so an extra field would fail it.

`id` comes last in the JSON because `Agreement` adds it after the creation fields. JSON clients don't depend on field order, but I can put `id` first to mirror the spec's POST example if you prefer.

## Part 3 prompts

### Prompt 1

> Part 3. Reconciling the gateway file
> Take one month of gateway rows, compare them with the invoices the schedule expects that month, and give each row a verdict.
>
> POST /reconciliation/runs
> { "month": "2026-10",
>   "rows": [
>     { "gateway_txn_id": "T-88121", "agreement_id": "…", "amount": 34385,
>       "currency": "SAR", "status": "SETTLED", "attempted_on": "2026-10-01" },
>     { "gateway_txn_id": "T-88122", "agreement_id": "…", "amount": 26950,
>       "currency": "BHD", "status": "DECLINED", "attempted_on": "2026-10-02" } ] }
> → 201 { "id": "…", "month": "2026-10",
>         "summary": { "MATCHED": 1, "DUE_DAY_DRIFT": 0, "DOUBLE_CHARGE_RISK": 0,
>                      "MISSING_FROM_LEDGER": 0, "DECLINED": 1 },
>         "rows": [ { "gateway_txn_id": "T-88121", "verdict": "MATCHED",
>                     "invoice": { "agreement_id": "…", "invoice_no": 2 } },
>                   { "gateway_txn_id": "T-88122", "verdict": "DECLINED", "invoice": null } ],
>         "unmatched_invoices": [ { "agreement_id": "…", "invoice_no": 2,
>                                   "due_date": "2026-10-01", "total": 26950, "currency": "BHD" } ] }
>
> GET /reconciliation/runs/{id} → 200 the same body
> Rows
> amount is a positive integer in minor units and is compared with the invoice total, VAT included.
> status is SETTLED or DECLINED.
> agreement_id is always present but may not exist in your store.
> Validation
> The whole request fails with 422 INVALID_ROWS when any row breaks one of these rules. Add "errors": [{"gateway_txn_id": "…", "code": "…"}] inside error, with one entry per offending row and code, in any order.
>
> DUPLICATE_TXN: added for every row whose gateway_txn_id appears more than once.
> ROW_OUTSIDE_MONTH: attempted_on is not in month.
> CURRENCY_MISMATCH: the row's agreement exists and its plan's currency differs from the row's. Rows with an unknown agreement skip this check.
> Matching
> Expected invoices are every invoice, from every agreement, whose due_date falls in month.
> Only SETTLED rows are matched. A row's candidates are its agreement's expected invoices whose total is within 1 minor unit of amount.
> Picking a candidate. With several candidates, take the earliest due date. Invoices already linked to another row still count.
> No candidate. An unknown agreement, or no candidate, makes the row MISSING_FROM_LEDGER.
> Order. The result must not depend on the order of rows in the request.
> Verdict	When
> MATCHED	The only settled row linked to its invoice, and attempted_on equals the invoice's due_date.
> DUE_DAY_DRIFT	The only settled row linked to its invoice, and attempted_on is a different day.
> DOUBLE_CHARGE_RISK	Two or more settled rows are linked to the same invoice. Every one of them gets this verdict.
> MISSING_FROM_LEDGER	No candidate, as above.
> DECLINED	The row's status is DECLINED. It takes no part in matching.
> Response
> summary has a key for every verdict, including zeros.
> rows come back in request order, with invoice set to {agreement_id, invoice_no} or null.
> unmatched_invoices lists expected invoices that no settled row is linked to. Sort by due_date, then agreement_id, then invoice_no. An invoice whose only rows were declined belongs here.
> A run is stored and can be read back by id. It never changes members or agreements.
>
> Similar to the previous parts, I want to build the data model first. In this case, it would be for the reconciliation runs, and consider the fields for each run, which is in this case the month, which includes the month and the year, and the rows which follow a certain structure. And you can maybe create a separate class for the structure, so you could say maybe gateway run, and or gateway row, gateway row, and each row consists of an ID in that format, or just maybe use the previous format that that was used for the member. And the next field for the row is the agreement ID, the amount, the currency, the status, which could be settled or declined only, attempted on, which is a date that follows the same format as the previous parts. Few things to keep in mind: that the ID for the gateway transaction or row must be unique, so it's not allowed to be duplicate. The row is expected to be inside the month, and if it's not inside the month, then the request fails. And the currency, if there's a mismatch between the currency of the row and the currency of the invoice, then the request also fails. This is for the validation, yeah? Now for matching make sure to add the check in the endpoint the post endpoint for the reconciliation runs. Which one for matching it checks the due date of every invoice that matches the month submitted in the run. The second is add a check that each for each settled row the invoice of the agreement is within 1 minor unit of the amount. And if it is not, then it is not matched. It should be labeled as unmatched.

**Response**

Built the reconciliation data models in `app/models/reconciliation.py`, with the three row rules as model validation. The endpoints and the matching rules aren't built yet; they're next. All 239 tests pass.

Request models:
- **`GatewayRow`:** `gateway_txn_id` (str), `agreement_id` (str), `amount` (strict integer > 0, minor units with VAT), `currency` (str), `status` (`SETTLED` or `DECLINED` only), `attempted_on` (`YYYY-MM-DD`, same type as Part 2).
- **`ReconciliationRunRequest`:** `month` and `rows: list[GatewayRow]`. `month` uses a new `IsoMonth` type in `app/models/types.py`: text shaped exactly `YYYY-MM`, month 01 to 12, kept as text. A malformed month or row is 422 `VALIDATION`.
- **`ReconciliationRunCreation`:** the same fields plus the row rules. It reports every offending row in one 422 `INVALID_ROWS`, one entry per row and code:
  - `DUPLICATE_TXN` for every row whose `gateway_txn_id` appears more than once, so two copies give two entries.
  - `ROW_OUTSIDE_MONTH` when `attempted_on` isn't in `month`.
  - `CURRENCY_MISMATCH` when the row's agreement exists and its plan's currency differs. Unknown agreements skip this check.

Response models:
- `InvoiceReference` (`agreement_id`, `invoice_no`).
- `RowResult` (`gateway_txn_id`, `verdict`, `invoice` or null).
- `VerdictSummary`: all five verdicts as required fields, so zeros are always present.
- `UnmatchedInvoice` (`agreement_id`, `invoice_no`, `due_date`, `total`, `currency`).
- `ReconciliationRun` (`id`, `month`, `summary`, `rows`, `unmatched_invoices`).

Three things to know:
- **Currency check needs the endpoint.** A model can't read the database, so the endpoint will look up each row's agreement currency and pass it in as validation context. All three rules then fail together in one error list rather than stopping at the first rule.
- **Error shape.** `app/helpers/errors.py` now maps `invalid_rows` to `INVALID_ROWS` and copies the `errors` list inside `error`. I checked it gives the contract shape: `{"error": {"code": "INVALID_ROWS", "message": "invalid rows", "errors": [{"gateway_txn_id": "T-1", "code": "DUPLICATE_TXN"}, …]}}`.
- **IDs.** `gateway_txn_id` is kept as the gateway sends it (e.g. `T-88121`), since it comes from the gateway. The run's own `id` will be generated in base62 like members and agreements.

When I build `POST /reconciliation/runs`, the matching goes there as you described:
- Expected invoices are the ones whose due date falls in the month.
- A settled row matches an invoice whose total is within 1 minor unit of its amount.
- A row with no candidate gets the verdict `MISSING_FROM_LEDGER`, the spec's name for unmatched.

Tests are in `tests/test_reconciliation_models.py`.

### Prompt 2

> Okay, now build the post and the get endpoints.

**Response**

Built `POST /reconciliation/runs` and `GET /reconciliation/runs/{id}`. All 270 tests pass, and both Docker stages build; the server image answers `/health` and a POST run.

How `POST /reconciliation/runs` works (`app/endpoints/reconciliation.py`):
1. FastAPI checks the body's shape with `ReconciliationRunRequest`. A malformed month or row returns 422 `VALIDATION`.
2. It looks up the plan currency of each row's agreement. Unknown agreements are left out, so they skip the currency check.
3. It validates `ReconciliationRunCreation` with those currencies. Any duplicate, out-of-month, or currency-mismatched row fails the whole request with 422 `INVALID_ROWS`, listing every offending row and code. Nothing is stored.
4. It works out the expected invoices: every invoice, from every agreement, whose due date falls in the month, computed by the Part 2 schedule.
5. It matches the rows (`app/helpers/reconciliation.py`):
   - A declined row is `DECLINED` and is not linked to an invoice.
   - A settled row's candidates are its agreement's expected invoices whose total is within 1 minor unit of the amount (`AMOUNT_TOLERANCE_MINOR_UNITS` in config). It is linked to the candidate with the earliest due date, even if that invoice is already linked to another row.
   - With no candidate, or an unknown agreement, the row is `MISSING_FROM_LEDGER`.
   - Two or more settled rows on one invoice are all `DOUBLE_CHARGE_RISK`. A single row is `MATCHED` if `attempted_on` equals the due date, otherwise `DUE_DAY_DRIFT`.
6. It builds the response:
   - `summary` counts all five verdicts, zeros included.
   - `rows` come back in request order.
   - `unmatched_invoices` are the expected invoices with no settled row, sorted by due date, then agreement id, then invoice number.
7. It gives the run a base62 id, stores the whole body as JSON in a new `reconciliation_runs` table, and returns 201.

Each row is linked on its own before verdicts are counted, so the result doesn't depend on row order.

`GET /reconciliation/runs/{id}` returns the stored body unchanged, or 404 `NOT_FOUND`.

Other changes:
- `UnmatchedInvoice` is renamed to `ExpectedInvoice`, because the same model holds every expected invoice before the unmatched ones are filtered out.
- `database.py` gained `fetch_all`, `list_plans`, `list_agreements`, `find_agreement_currency` and the run insert and find queries.

Tests are in `tests/test_reconciliation.py`. They cover:
- the spec example and the GET round trip
- each verdict, and the ±1 minor unit edges
- declined-only invoices, the unmatched sort, and row-order independence
- the `INVALID_ROWS` lists, malformed bodies, and concurrent runs

The year-9999 limit from Part 2 also applies here: a run for month `9999-12` would return 500.
