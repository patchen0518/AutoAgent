import base64
import io
import logging
import re
from typing import Dict, List, Optional

import numpy as np
import PIL.Image

logger = logging.getLogger(__name__)

BID_ATTR = "browsergym_id"
VIS_ATTR = "browsergym_visibility" 
SOM_ATTR = "browsergym_set_of_marks"

class MarkingError(Exception):
    pass

def ensure_cdp_activated(browser):
    """确保CDP模式已激活"""
    if not hasattr(browser, 'cdp') or browser.cdp is None:
        current_url = browser.get_current_url()
        browser.activate_cdp_mode(current_url if current_url else "about:blank")
        browser.sleep(1)  # 等待CDP模式激活

def _pre_extract(browser):
    """标记DOM元素"""
    try:
        ensure_cdp_activated(browser)
        
        # 定义并注入标记函数
        browser.cdp.evaluate("""
        window.markElements = function(frameBid='') {
            function markElementsInDocument(doc, bid_prefix='') {
                const elements = doc.getElementsByTagName('*');
                for (let element of elements) {
                    if (!element.hasAttribute('browsergym_id')) {
                        const bid = bid_prefix + element.tagName.toLowerCase() + '_' + 
                                  Math.random().toString(36).substr(2, 9);
                        element.setAttribute('browsergym_id', bid);
                    }
                }
                
                // 递归处理所有iframe
                const iframes = doc.getElementsByTagName('iframe');
                for (let iframe of iframes) {
                    try {
                        const frameDoc = iframe.contentDocument;
                        if (frameDoc) {
                            const frameBid = iframe.getAttribute('browsergym_id') || '';
                            const sandbox = iframe.getAttribute('sandbox');
                            if (!sandbox || sandbox.includes('allow-scripts')) {
                                markElementsInDocument(frameDoc, frameBid);
                            }
                        }
                    } catch (e) {
                        // 跨域iframe会抛出错误，忽略即可
                        console.log('Cannot access iframe:', e);
                    }
                }
            }
            
            // 从当前文档开始标记
            markElementsInDocument(document, frameBid);
            
            return true;
        };
        """)
        
        # 执行标记
        success = browser.cdp.evaluate("window.markElements()")
        if not success:
            raise MarkingError("Failed to mark elements")
            
    except Exception as e:
        raise MarkingError(f"Error marking elements: {str(e)}")

def extract_dom_snapshot(browser):
    """获取DOM快照"""
    try:
        ensure_cdp_activated(browser)
        
        # 定义函数
        browser.cdp.evaluate("""
        window.getDOMSnapshot = function() {
            const strings = new Map();
            let stringId = 0;
            
            function getStringId(str) {
                if (str === null || str === undefined) return -1;
                if (!strings.has(str)) {
                    strings.set(str, stringId++);
                }
                return strings.get(str);
            }
            
            function processDocument(doc) {
                function processNode(node, parentIndex) {
                    const nodeData = {
                        nodeType: [],
                        nodeName: [],
                        nodeValue: [],
                        parentIndex: [],
                        attributes: [],
                        contentDocumentIndex: {
                            index: [],
                            value: []
                        }
                    };
                    
                    nodeData.nodeType.push(node.nodeType);
                    nodeData.nodeName.push(getStringId(node.nodeName));
                    nodeData.nodeValue.push(getStringId(node.nodeValue));
                    nodeData.parentIndex.push(parentIndex);
                    
                    const attrs = [];
                    if (node.attributes) {
                        for (let attr of node.attributes) {
                            attrs.push(getStringId(attr.name));
                            attrs.push(getStringId(attr.value));
                        }
                    }
                    nodeData.attributes.push(attrs);
                    
                    if (node.nodeType === 1) { // Element node
                        const iframes = node.getElementsByTagName('iframe');
                        for (let i = 0; i < iframes.length; i++) {
                            try {
                                const frameDoc = iframes[i].contentDocument;
                                if (frameDoc) {
                                    nodeData.contentDocumentIndex.index.push(nodeData.nodeType.length - 1);
                                    nodeData.contentDocumentIndex.value.push(1); // Assuming single document for now
                                }
                            } catch (e) {
                                console.log('Cannot access iframe:', e);
                            }
                        }
                    }
                    
                    for (let child of node.childNodes) {
                        const childData = processNode(child, nodeData.nodeType.length - 1);
                        
                        nodeData.nodeType.push(...childData.nodeType);
                        nodeData.nodeName.push(...childData.nodeName);
                        nodeData.nodeValue.push(...childData.nodeValue);
                        nodeData.parentIndex.push(...childData.parentIndex);
                        nodeData.attributes.push(...childData.attributes);
                        nodeData.contentDocumentIndex.index.push(...childData.contentDocumentIndex.index);
                        nodeData.contentDocumentIndex.value.push(...childData.contentDocumentIndex.value);
                    }
                    
                    return nodeData;
                }
                
                return processNode(doc.documentElement, -1);
            }
            
            const rootData = processDocument(document);
            const stringsArray = Array.from(strings.keys());
            
            return {
                documents: [{
                    nodes: rootData
                }],
                strings: stringsArray
            };
        };
        """)
        
        # 执行函数
        dom_snapshot = browser.cdp.evaluate("window.getDOMSnapshot()")
        
        return dom_snapshot
        
    except Exception as e:
        logger.error(f"Error capturing DOM snapshot: {str(e)}")
        return {"documents": [], "strings": []}

def extract_dom_extra_properties(browser) -> Dict:
    """获取DOM元素的有意义的额外属性"""
    try:
        ensure_cdp_activated(browser)
        
        browser.cdp.evaluate("""
        window.getExtraProperties = function() {
            const BID_ATTR = 'browsergym_id';
            const VIS_ATTR = 'browsergym_visibility';
            const SOM_ATTR = 'browsergym_set_of_marks';
            
            // 定义重要的标签和属性
            const IMPORTANT_TAGS = new Set([
                'A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA', 'FORM',
                'IMG', 'VIDEO', 'AUDIO', 'IFRAME', 'LABEL', 'H1', 'H2', 
                'H3', 'H4', 'H5', 'H6'
            ]);
            
            const IMPORTANT_ROLES = new Set([
                'button', 'link', 'checkbox', 'radio', 'textbox', 'combobox',
                'listbox', 'menu', 'menuitem', 'tab', 'tabpanel', 'tree',
                'treeitem', 'dialog', 'alert', 'alertdialog', 'tooltip'
            ]);
            
            function isElementVisible(element) {
                const style = window.getComputedStyle(element);
                return style.display !== 'none' && 
                       style.visibility !== 'hidden' && 
                       style.opacity !== '0' &&
                       element.offsetWidth > 0 &&
                       element.offsetHeight > 0;
            }
            
            function isElementInteractive(element) {
                // 检查是否可交互
                return element.onclick !== null ||
                       element.onmousedown !== null ||
                       element.onmouseup !== null ||
                       element.onkeydown !== null ||
                       element.onkeyup !== null ||
                       element.onchange !== null ||
                       element.onfocus !== null ||
                       element.onblur !== null;
            }
            
            function isElementMeaningful(element) {
                // 检查标签是否重要
                if (IMPORTANT_TAGS.has(element.tagName)) return true;
                
                // 检查角色是否重要
                const role = element.getAttribute('role');
                if (role && IMPORTANT_ROLES.has(role)) return true;
                
                // 检查是否有重要的ARIA属性
                if (element.hasAttribute('aria-label')) return true;
                if (element.hasAttribute('aria-description')) return true;
                
                // 检查是否可交互
                if (isElementInteractive(element)) return true;
                
                // 检查是否有有意义的文本内容
                const text = element.textContent.trim();
                if (text && text.length > 1 && !/^[\s\d.,]+$/.test(text)) return true;
                
                // 检查是否有有意义的图片
                if (element.tagName === 'IMG' && element.alt) return true;
                
                return false;
            }
            
            function getDocumentProperties(doc, parentFrame = null) {
                const properties = {};
                const frameOffset = {
                    x: 0,
                    y: 0
                };
                
                if (parentFrame) {
                    const frameRect = parentFrame.getBoundingClientRect();
                    frameOffset.x = frameRect.x + window.pageXOffset;
                    frameOffset.y = frameRect.y + window.pageYOffset;
                }
                
                const elements = doc.querySelectorAll(`[${BID_ATTR}]`);
                
                elements.forEach(element => {
                    // 只处理有意义的元素
                    if (!isElementMeaningful(element)) return;
                    
                    // 只处理可见元素
                    if (!isElementVisible(element)) return;
                    
                    const bid = element.getAttribute(BID_ATTR);
                    if (!bid) return;
                    
                    let visibility = element.getAttribute(VIS_ATTR);
                    visibility = visibility ? parseFloat(visibility) : 1.0;
                    
                    const rect = element.getBoundingClientRect();
                    const bbox = rect ? [
                        rect.x + window.pageXOffset + frameOffset.x,
                        rect.y + window.pageYOffset + frameOffset.y,
                        rect.width,
                        rect.height
                    ] : null;
                    
                    // 更精确的可点击检测
                    const isClickable = (
                        element.tagName === 'BUTTON' ||
                        element.tagName === 'A' ||
                        (element.tagName === 'INPUT' && 
                         ['button', 'submit', 'reset', 'radio', 'checkbox'].includes(element.type)) ||
                        element.getAttribute('role') === 'button' ||
                        isElementInteractive(element) ||
                        window.getComputedStyle(element).cursor === 'pointer'
                    );
                    
                    const setOfMarks = element.getAttribute(SOM_ATTR) === '1';
                    
                    // 添加额外的有用信息
                    const extraInfo = {
                        tag: element.tagName.toLowerCase(),
                        type: element.type || null,
                        role: element.getAttribute('role') || null,
                        text: element.textContent.trim() || null,
                        ariaLabel: element.getAttribute('aria-label') || null
                    };
                    
                    properties[bid] = {
                        visibility: visibility,
                        bbox: bbox,
                        clickable: isClickable,
                        set_of_marks: setOfMarks,
                        ...extraInfo
                    };
                });
                
                // 递归处理iframe
                const iframes = doc.getElementsByTagName('iframe');
                for (let iframe of iframes) {
                    try {
                        const frameDoc = iframe.contentDocument;
                        if (frameDoc) {
                            const frameProperties = getDocumentProperties(frameDoc, iframe);
                            Object.assign(properties, frameProperties);
                        }
                    } catch (e) {
                        console.log('Cannot access iframe:', e);
                    }
                }
                
                return properties;
            }
            
            return getDocumentProperties(document);
        };
        """)
        
        extra_properties = browser.cdp.evaluate("window.getExtraProperties()")
        return extra_properties
        
    except Exception as e:
        logger.error(f"Error extracting extra properties: {str(e)}")
        return {}

def extract_merged_axtree(browser):
    """获取更清晰的Accessibility Tree"""
    try:
        ensure_cdp_activated(browser)
        
        browser.cdp.evaluate("""
        window.getAccessibilityTree = function() {
            let nodeId = 1;
            
            // 需要忽略的角色
            const IGNORED_ROLES = new Set([
                'generic',
                'presentation',
                'none',
                'ScrollBar',
                'background'
            ]);
            
            // 需要保留的HTML标签
            const IMPORTANT_TAGS = new Set([
                'a', 'button', 'input', 'select', 'textarea', 'header', 
                'nav', 'main', 'footer', 'form', 'table', 'iframe',
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
            ]);
            
            function getElementRole(element) {
                // 优先使用aria角色
                const ariaRole = element.getAttribute('role');
                if (ariaRole) return ariaRole;
                
                // 特殊元素的默认角色
                const tagName = element.tagName.toLowerCase();
                switch (tagName) {
                    case 'a': return 'link';
                    case 'button': return 'button';
                    case 'input': 
                        const type = element.type;
                        if (type === 'checkbox') return 'checkbox';
                        if (type === 'radio') return 'radio';
                        if (type === 'submit') return 'button';
                        return 'textbox';
                    case 'select': return 'combobox';
                    case 'textarea': return 'textbox';
                    case 'img': return 'img';
                    case 'table': return 'table';
                    default: return tagName;
                }
            }
            
            function getElementName(element) {
                // 按优先级获取元素名称
                return element.getAttribute('aria-label') ||
                       element.getAttribute('title') ||
                       element.getAttribute('alt') ||
                       element.getAttribute('name') ||
                       element.value ||
                       element.textContent.trim();
            }
            
            function shouldIncludeElement(element) {
                const tagName = element.tagName.toLowerCase();
                const role = getElementRole(element);
                
                // 检查是否是重要标签
                if (IMPORTANT_TAGS.has(tagName)) return true;
                
                // 检查是否有重要属性
                if (element.getAttribute('aria-label')) return true;
                if (element.getAttribute('role')) return true;
                if (element.onclick) return true;
                
                // 检查是否可交互
                const style = window.getComputedStyle(element);
                if (style.cursor === 'pointer') return true;
                
                // 忽略无用角色
                if (IGNORED_ROLES.has(role)) return false;
                
                // 忽略空文本节点
                const text = element.textContent.trim();
                if (!text) return false;
                
                return true;
            }
            
            function processNode(element) {
                if (!shouldIncludeElement(element)) return null;
                
                const role = getElementRole(element);
                const name = getElementName(element);
                
                // 如果既没有有效的角色也没有名称，则跳过
                if ((!role || IGNORED_ROLES.has(role)) && !name) return null;
                
                const node = {
                    nodeId: nodeId++,
                    role: { value: role },
                    name: { value: name },
                    properties: [],
                    childIds: [],
                    backendDOMNodeId: element.getAttribute('browsergym_id') || null,
                    frameId: element.ownerDocument?.defaultView?.frameElement?.getAttribute('browsergym_id') || null
                };
                
                // 收集重要的ARIA属性
                for (let attr of element.attributes) {
                    if (attr.name.startsWith('aria-')) {
                        node.properties.push({
                            name: { value: attr.name },
                            value: { value: attr.value }
                        });
                    }
                }
                
                // 递归处理子元素
                for (let child of element.children) {
                    const childNode = processNode(child);
                    if (childNode) {
                        node.childIds.push(childNode.nodeId);
                    }
                }
                
                return node;
            }
            
            const nodes = [];
            function traverse(element) {
                const node = processNode(element);
                if (node) {
                    nodes.push(node);
                    for (let child of element.children) {
                        traverse(child);
                    }
                }
            }
            
            traverse(document.documentElement);
            
            return { nodes: nodes };
        };
        """)
        
        axtree = browser.cdp.evaluate("window.getAccessibilityTree()")
        return axtree
        
    except Exception as e:
        logger.error(f"Error getting accessibility tree: {str(e)}")
        return {"nodes": []}