import requests
import json

def summarize_text_claude(text):
    API_KEY = "CLAUDE_PDF_SUMMARY_KEY"
    API_URL = "https://api.anthropic.com/v1/messages"

    payload = {
        "model": "claude-3-sonnet-20240229", 
        "max_tokens": 1000, 
        "temperature": 0.3,
        "messages": [
            {
                "role": "user",
                "content": f"Summarize this text: {text}"
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
        "anthropic-version": "2023-06-01"
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        summary = result['content'][0]['text']
        print("Summary:")
        print(summary)
    else:
        print(f"Error: {response.status_code}")
        print(json.dumps(response.json(), indent=2))

# Example usage
text_to_summarize = """
The Internet of Things (IoT) is a network of interconnected physical devices, vehicles, home appliances, and other items embedded with electronics, software, sensors, actuators, and network connectivity which enable these objects to collect and exchange data. The IoT allows objects to be sensed or controlled remotely across existing network infrastructure, creating opportunities for more direct integration of the physical world into computer-based systems, and resulting in improved efficiency, accuracy, and economic benefit in addition to reduced human intervention.

The concept of a network of smart devices was discussed as early as 1982, with a modified Coca-Cola machine at Carnegie Mellon University becoming the first internet-connected appliance, able to report its inventory and whether newly loaded drinks were cold. In 1999, Kevin Ashton of the Auto-ID Center at MIT first used the term "Internet of Things" in the context of supply chain management. Today, the IoT has evolved into a vast ecosystem of technologies, impacting everything from smart homes and cities to industrial manufacturing and healthcare.

The rapid growth of IoT is driven by several factors: the decreasing cost and size of sensors, the widespread availability of Wi-Fi and cellular networks, advancements in cloud computing, and the rise of big data analytics. As these technologies converge, they're enabling an ever-growing number of devices to communicate and share data without human involvement. By 2025, it's estimated that there will be more than 75 billion IoT devices worldwide.

However, the IoT also presents significant challenges. Security is a major concern, as each connected device represents a potential entry point for cybercriminals. Privacy issues also abound, with devices collecting vast amounts of personal data. There are also questions of standardization, as different manufacturers may use different protocols, making interoperability a challenge. Furthermore, as our reliance on IoT grows, so does our vulnerability to system failures or cyberattacks that could disrupt critical infrastructure.

Despite these challenges, the potential benefits of IoT are immense. In healthcare, wearable devices can monitor patients remotely, allowing for early detection of issues. In agriculture, IoT sensors can optimize irrigation and fertilizer use. In cities, IoT can manage traffic flows, reduce energy consumption, and even help cut crime. For consumers, smart homes offer convenience, energy savings, and enhanced security. The industrial IoT promises to revolutionize manufacturing through predictive maintenance and real-time optimization of production lines.

As we move forward, the evolution of 5G networks and advances in AI are set to further boost the IoT's capabilities. 5G's high speeds and low latency will enable real-time control of devices, even in critical applications like autonomous vehicles or remote surgery. AI, particularly machine learning, will help make sense of the vast data IoT devices generate, turning it into actionable insights. The future of IoT is not just about connectivity, but about creating a world that's smarter, more efficient, and hopefully, more sustainable.
"""

summarize_text_claude(text_to_summarize)