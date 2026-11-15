"""Part 1 test: register a member, then look the member up by phone in every spelling."""
from tests.conftest import member_body, paint, print_detail, print_part_header, print_passed, print_section, report


def test_register_and_look_up_member(client):
    print_part_header("PART 1 - Members and phones")

    print_section("Register")
    registration = member_body(name="Noura Al Harbi", country="SA", phone="055 123 4567")
    response = client.post("/members", json=registration)
    report(1, "POST", "/members", "Noura Al Harbi, SA, phone 055 123 4567", response)
    member = response.json()
    assert response.status_code == 201
    assert member == {"id": member["id"], "name": "Noura Al Harbi", "country": "SA", "phone": "+966551234567"}
    print_detail(f"id     {member['id']}")
    print_detail(f"phone  {paint(member['phone'], 'bold')}  (stored in E.164)")

    print_section("Look up by phone, every spelling")
    lookup_spellings = [
        ("dial code without +", {"phone": "966551234567"}),
        ("dial code with +", {"phone": "+966551234567"}),
        ("national number with country SA", {"phone": "055 123 4567", "country": "SA"}),
    ]
    for step_number, (spelling, parameters) in enumerate(lookup_spellings, start=2):
        response = client.get("/members/lookup", params=parameters)
        report(step_number, "GET", f"/members/lookup  {parameters}", spelling, response)
        assert response.status_code == 200
        assert response.json() == member
        print_detail(f"found  {paint(response.json()['name'], 'bold')}")

    print_section("Rejected requests")
    second_registration = member_body(name="Sara", country="SA", phone="+966 (55) 123-4567")
    response = client.post("/members", json=second_registration)
    report(5, "POST", "/members", "Sara, SA, +966 (55) 123-4567: Noura's number in another spelling", response)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PHONE_TAKEN"
    assert response.json()["error"]["existing_member_id"] == member["id"]
    print_detail(f"existing_member_id  {response.json()['error']['existing_member_id']}")

    response = client.get("/members/lookup", params={"phone": "0551234567"})
    report(6, "GET", "/members/lookup  {'phone': '0551234567'}", "national number without a country", response)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "PHONE_NEEDS_COUNTRY"

    response = client.get("/members/lookup", params={"phone": "+966559999999"})
    report(7, "GET", "/members/lookup  {'phone': '+966559999999'}", "a number nobody has", response)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"

    print_passed("Part 1")
