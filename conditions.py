def if_image_tags(img_tags, web_address, key):
    links = []
    for img_tag in img_tags:
        img_src = img_tag.get("src")
        if "svg" in str(img_src):
            img_src = img_tag.get("data-src")
        if img_src:
            if img_src[0] == "/" and img_src[1] != "/":
                web_addresss = str(web_address)[:-1]
                img_src = f"{web_addresss}{img_src}"
                img_src.replace(" ", "")
            else:
                img_src = str(img_src).replace("//images", "https://images")
                substring_to_count = "https://"
                replacement_substring = "/"
                count = img_src.count(substring_to_count)
                if count >= 2:
                    last_occurrence_index = img_src.rfind(substring_to_count)
                    img_src = (
                        img_src[:last_occurrence_index]
                        + replacement_substring
                        + img_src[last_occurrence_index + len(substring_to_count) :]
                    )
            if (
                {key: f"{img_src}"} not in links
                and "svg" not in str(img_src)
                and "gif" not in str(img_src)
            ):
                img_src = img_src.replace(" ", "")
                links.append({key: f"{img_src}"})
    if links is None:
        return {key: "LOGO NOT FOUND"}
    return links


def if_images_with_school_name(images_with_school_name, web_address, key):
    links = []
    for img_tag in images_with_school_name:
        img_src = img_tag.get("src")
        if "svg" in str(img_src):
            img_src = img_tag.get("data-src")
        if img_src:
            if img_src[0] == "/" and img_src[1] != "/":
                web_addresss = str(web_address)[:-1]
                img_src = f"{web_addresss}{img_src}"
                img_src.replace(" ", "")
            else:
                img_src = str(img_src).replace("//images", "https://images")
                substring_to_count = "https://"
                replacement_substring = "/"
                count = img_src.count(substring_to_count)
                if count >= 2:
                    last_occurrence_index = img_src.rfind(substring_to_count)
                    img_src = (
                        img_src[:last_occurrence_index]
                        + replacement_substring
                        + img_src[last_occurrence_index + len(substring_to_count) :]
                    )
            if (
                {key: f"{img_src}"} not in links
                and "svg" not in str(img_src)
                and "gif" not in str(img_src)
            ):
                img_src = img_src.replace(" ", "")
                links.append({key: f"{img_src}"})
    if links is None:
        return {key: "LOGO NOT FOUND"}
    return links


def if_image_tags_in_anchor(image_tags_in_anchor, web_address, key):
    links = []
    for img_tag in image_tags_in_anchor:
        if img_tag.get("data-src"):
            img_src = img_tag.get("data-src")
        else:
            img_src = img_tag.get("src")
        if "svg" in str(img_src):
            img_src = img_tag.get("data-src")
        if img_src:
            if img_src[0] == "/" and img_src[1] != "/":
                web_addresss = str(web_address)[:-1]
                img_src = f"{web_addresss}{img_src}"
                img_src.replace(" ", "")
            else:
                img_src = str(img_src).replace("//images", "https://images")
                substring_to_count = "https://"
                replacement_substring = "/"
                count = img_src.count(substring_to_count)
                if count >= 2:
                    last_occurrence_index = img_src.rfind(substring_to_count)
                    img_src = (
                        img_src[:last_occurrence_index]
                        + replacement_substring
                        + img_src[last_occurrence_index + len(substring_to_count) :]
                    )
            if (
                {key: f"{img_src}"} not in links
                and "svg" not in str(img_src)
                and "gif" not in str(img_src)
            ):
                img_src = img_src.replace(" ", "")
                links.append({key: f"{img_src}"})
    if links is None:
        return {key: "LOGO NOT FOUND"}
    return links


def if_header_img(header_img, web_address, key):
    links = []
    img_src = header_img.get("src")
    if "svg" in str(img_src):
        img_src = header_img.get("data-src")
    if img_src:
        if img_src[0] == "/" and img_src[1] != "/":
            web_addresss = str(web_address)[:-1]
            img_src = f"{web_addresss}{img_src}"
            img_src.replace(" ", "")
        else:
            img_src = str(img_src).replace("//images", "https://images")
            substring_to_count = "https://"
            replacement_substring = "/"
            count = img_src.count(substring_to_count)
            if count >= 2:
                last_occurrence_index = img_src.rfind(substring_to_count)
                img_src = (
                    img_src[:last_occurrence_index]
                    + replacement_substring
                    + img_src[last_occurrence_index + len(substring_to_count) :]
                )
        if (
            {key: f"{img_src}"} not in links
            and "svg" not in str(img_src)
            and "gif" not in str(img_src)
        ):
            img_src = img_src.replace(" ", "")
            links.append({key: f"{img_src}"})
    if links is None:
        return {key: "LOGO NOT FOUND"}
    return links


def if_image_in_headers_anchor(header_anchor_with_image, web_address, key):
    links = []
    for anchor in header_anchor_with_image:
        if "www." in str(
            anchor.find_parent("a")["href"]
        ) and "www." not in web_address.rstrip("/"):
            href = str(anchor.find_parent("a")["href"]).replace("www.", "")
            if web_address.rstrip("/") in href:
                links.append({key: f"{anchor['src']}"})
        elif web_address.rstrip("/") in str(anchor.find_parent("a")["href"]):
            links.append({key: f"{anchor['src']}"})
    if links is None:
        return {key: "LOGO NOT FOUND"}
    return links
