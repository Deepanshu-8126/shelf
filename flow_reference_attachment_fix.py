import asyncio
from pathlib import Path
from playwright.async_api import Page

async def remove_chip_by_filename(page: Page, target_filename: str):
    """
    Finds and removes an image ingredient chip from the Flow prompt box
    either by matching filename in image alt/src/title or removes the specific chip index.
    """
    stem = Path(target_filename).stem.lower()
    chips = await page.locator('flow-base-prompt-box flow-image-ingredient-chip').all()
    print(f"🔍 [Flow Attachment] Checking {len(chips)} active chips for removal target: {stem}")
    
    removed = False
    for i, chip in enumerate(chips):
        text = (await chip.inner_text()).lower()
        # Also check img attributes
        img = chip.locator('img').first
        src = (await img.get_attribute('src') or "").lower() if await img.count() > 0 else ""
        alt = (await img.get_attribute('alt') or "").lower() if await img.count() > 0 else ""
        
        if stem in text or stem in src or stem in alt or target_filename.lower() in text:
            print(f"  ❌ Removing chip [{i}] matching '{target_filename}'...")
            await chip.locator('button.chip-container').first.hover()
            cancel_icon = chip.locator('mat-icon:has-text("cancel")').first
            if await cancel_icon.count() > 0:
                await cancel_icon.click(force=True)
                await asyncio.sleep(1.0)
                removed = True
                break
                
    # If not found by name, and caller wants to remove the second chip (old character sheet):
    if not removed and len(chips) >= 2 and target_filename == "OLD_CHARACTER_SHEET_FILENAME.jpg":
        print("  ❌ Target name generic: Removing second chip as fallback...")
        await chips[1].locator('button.chip-container').first.hover()
        cancel_icon = chips[1].locator('mat-icon:has-text("cancel")').first
        if await cancel_icon.count() > 0:
            await cancel_icon.click(force=True)
            await asyncio.sleep(1.0)


async def attach_flow_library_image(page: Page, image_path: Path or str):
    """
    Opens the Google Flow ingredients library and attaches the given image
    to the active prompt box.
    """
    target_name = Path(image_path).name if isinstance(image_path, (Path, str)) else str(image_path)
    target_stem = Path(target_name).stem
    
    print(f"📎 [Flow Attachment] Attaching reference asset: {target_name} ({target_stem})...")
    
    # 1. Open ingredients menu safely
    add_btn = page.locator('button.add-menu-trigger, button[aria-label="Add ingredients to the prompt box"], button[aria-label*="ingredient" i]').first
    if await add_btn.count() > 0 and await add_btn.is_visible():
        try:
            await add_btn.click(timeout=3000)
            await asyncio.sleep(1.5)
        except Exception as btn_err:
            print(f"  ℹ️ Add button click notice: {btn_err}")
    else:
        print("  ℹ️ Ingredient menu trigger not visible or already set. Continuing...")
    
    # 2. Look for the asset in the overlay
    overlay = page.locator('.cdk-overlay-container')
    item = overlay.locator(f'button.asset-item:has-text("{target_stem}"), button.asset-item:has-text("{target_name}")').first
    
    if await item.count() > 0:
        print(f"  Found '{target_stem}' in Flow Asset Library! Selecting...")
        await item.click()
        await asyncio.sleep(1.0)
        
        # Click Add to prompt button if available
        add_to_prompt = overlay.locator('button:has-text("Add to prompt"), button.detail-add-to-prompt-btn').first
        if await add_to_prompt.count() > 0 and await add_to_prompt.is_visible():
            await add_to_prompt.click()
            await asyncio.sleep(1.5)
            print(f"  ✅ '{target_name}' attached to prompt box!")
    else:
        print(f"  ⚠️ Warning: Asset '{target_stem}' not found in current overlay view.")
        
    # Close any open overlay drawer
    await page.keyboard.press("Escape")
    await asyncio.sleep(1.0)
