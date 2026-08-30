import guava

from concierge_app import voice_styles

agent = guava.Agent(
    name=voice_styles.AGENT_NAME,
    organization=voice_styles.ORGANIZATION,
    purpose=voice_styles.get(voice_styles.DEFAULT_STYLE).purpose(),
)
