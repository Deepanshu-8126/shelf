# Photoshoot & Visual Aesthetic Engine Rules

## 1. Engine Priority & Model Tiering
- **Primary Generator**: LM Arena (`arena.ai/image`) is established as the gold standard for fashion photoshoot generation. Its neural models (FLUX.1, Ideogram, SD3.5) produce significantly higher fidelity, photorealism, and natural lighting compared to legacy engines.
- **Failover Chain**: If Arena is rate-limited or unauthenticated in automated headless workflows, seamlessly step through:
  1. LM Arena Fast Stealth Runner
  2. Google Flow Studio Engine
  3. Studio Neural Synthesizer (ModelFaceIdentityTrainer + UniversalLLMVisualTrainer)
- **Zero Process Stoppage**: Never allow timeouts or modal interruptions to terminate execution (`out_photo` is 100% guaranteed to return a valid image).

## 2. Optical Profile & Skin Preservation (Anti-Crunch Standard)
- **Zero Harsh Over-Sharpening**: Never apply digital unsharp masks > 15% or sharpness factors > 1.02.
- **Authentic Skin Texture**: Always preserve authentic skin pores, dewy golden-olive tones, and soft natural lighting.
- **Model Consistency**: Maintain signature 21yo Indian creator identity (warm honey-brown almond eyes, signature round black bindi, traditional oxidised silver jhumkas, wavy dark espresso hair).

## 3. High-Velocity Stealth Browser Automation
- **Micro-Polling**: Use 300ms DOM evaluation instead of static multi-second sleeps.
- **Stealth Interaction**: Use `human_move_and_click` (Bezier cursor path + micro-jitter) and clipboard injection (`navigator.clipboard.writeText` + `Ctrl+V`) to bypass bot detection without slowing down execution.
