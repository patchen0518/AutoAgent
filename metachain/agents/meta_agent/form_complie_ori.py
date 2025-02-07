

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

class AgentForm:
    def __init__(self, xml_string: str):
        # Parse XML string
        root = ET.fromstring(xml_string)
        
        # Parse system input/output
        self.system_input = root.find('system_input').text.strip()
        
        system_output = root.find('system_output')
        self.system_output = {
            'key': system_output.find('key').text.strip(),
            'description': system_output.find('description').text.strip()
        }
        
        # Parse global variables (optional)
        global_vars = root.find('global_variables')
        self.global_variables = {}
        if global_vars is not None:
            for var in global_vars.findall('variable'):
                self.global_variables[var.find('key').text.strip()] = {
                    'description': var.find('description').text.strip(),
                    'value': var.find('value').text.strip()
                }
        
        # Parse agents
        self.agents = []
        for agent_elem in root.findall('agent'):
            agent = {
                'name': agent_elem.find('name').text.strip(),
                'description': agent_elem.find('description').text.strip(),
                'instructions': agent_elem.find('instructions').text.strip(),
                
                # Parse tools
                'tools': {
                    'existing': [],
                    'new': []
                },
                
                # Parse agent input/output
                'input': {
                    'key': agent_elem.find('agent_input/key').text.strip(),
                    'description': agent_elem.find('agent_input/description').text.strip()
                },
                'output': {
                    'key': agent_elem.find('agent_output/key').text.strip(),
                    'description': agent_elem.find('agent_output/description').text.strip()
                }
            }
            
            # Parse tools for both existing and new categories
            for tools_category in agent_elem.findall('tools'):
                category = tools_category.get('category')
                for tool in tools_category.findall('tool'):
                    tool_info = {
                        'name': tool.find('name').text.strip(),
                        'description': tool.find('description').text.strip()
                    }
                    agent['tools'][category].append(tool_info)
            
            self.agents.append(agent)
    
    def validate(self) -> bool:
        """
        验证表单是否符合规则：
        1. system_output必须只有一个key-description对
        2. 每个agent的input/output必须只有一个key-description对
        3. 对于单agent系统，system in/output必须与agent in/output相同
        """
        try:
            # 检查是否为单agent系统
            if len(self.agents) == 1:
                agent = self.agents[0]
                # 检查system和agent的input/output是否匹配
                if agent['output']['key'] != self.system_output['key']:
                    return False
            
            # 检查每个agent的input/output格式
            for agent in self.agents:
                if not agent['input'].get('key') or not agent['input'].get('description'):
                    return False
                if not agent['output'].get('key') or not agent['output'].get('description'):
                    return False
            
            return True
        except Exception:
            return False
    
    def to_dict(self) -> Dict:
        """将表单转换为字典格式"""
        return {
            'system_input': self.system_input,
            'system_output': self.system_output,
            'global_variables': self.global_variables,
            'agents': self.agents
        }

# 使用示例
def parse_agent_form(xml_path: str) -> Optional[Dict]:
    """
    读取并解析agent form XML文件
    
    Args:
        xml_path: XML文件路径
    
    Returns:
        解析后的字典格式数据，如果解析失败返回None
    """
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        form = AgentForm(xml_content)
        if not form.validate():
            print("Error: Invalid agent form format")
            return None
            
        return form.to_dict()
    
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# 使用示例
if __name__ == "__main__":
    import json
    result = parse_agent_form("/Users/tangjiabin/Documents/reasoning/metachain/metachain/agents/meta_agent/agent_form/customer_service.xml")
    if result:
        print("Successfully parsed agent form:")
        print(json.dumps(result, indent=4))