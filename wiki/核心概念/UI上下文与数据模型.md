# UI上下文与数据模型

UI上下文与数据模型是 Midscene Python 的数据基础，定义了框架中所有数据结构、类型系统和上下文传递机制。理解这些数据模型对于深入使用框架至关重要。

## 🎯 设计理念

### 类型安全优先
Midscene Python 使用 Pydantic 和 Python 类型注解来确保数据的类型安全：

```python
from pydantic import BaseModel
from typing import List, Optional, Generic, TypeVar

class UIContext(BaseModel, Generic[ElementType]):
    """类型安全的 UI 上下文"""
    screenshot_base64: str
    size: Size
    content: List[ElementType]  # 泛型支持
```

### 跨平台统一抽象
相同的数据模型在不同平台（Web、Android）上保持一致的接口：

```python
# Web 和 Android 使用相同的数据模型
web_context: UIContext = await web_page.get_context()
android_context: UIContext = await android_device.get_context()

# 操作方式完全相同
print(web_context.screenshot_base64)
print(android_context.screenshot_base64)
```

## 🏗️ 核心数据模型

### 几何数据类型

#### Point (点)
```python
@dataclass
class Point:
    """2D 点坐标"""
    x: float
    y: float

# 使用示例
center_point = Point(x=100.5, y=200.0)
```

#### Size (尺寸)
```python
@dataclass
class Size:
    """尺寸信息"""
    width: float
    height: float

# 使用示例
viewport_size = Size(width=1920, height=1080)
```

#### Rect (矩形)
```python
@dataclass
class Rect:
    """矩形区域"""
    left: float
    top: float
    width: float
    height: float
    
    @property
    def right(self) -> float:
        return self.left + self.width
    
    @property
    def bottom(self) -> float:
        return self.top + self.height
    
    @property
    def center(self) -> Point:
        return Point(
            x=self.left + self.width / 2,
            y=self.top + self.height / 2
        )

# 使用示例
button_rect = Rect(left=100, top=200, width=120, height=40)
print(f"按钮中心: {button_rect.center}")  # Point(x=160.0, y=220.0)
print(f"按钮右边界: {button_rect.right}")  # 220.0
```

### UI 元素模型

#### BaseElement (基础元素)
```python
class BaseElement(BaseModel):
    """基础 UI 元素接口"""
    id: str                                    # 元素唯一标识
    content: str                              # 元素文本内容
    rect: Rect                                # 元素位置和大小
    center: tuple[float, float]               # 元素中心点
    node_type: NodeType = NodeType.OTHER      # 元素类型
    attributes: Dict[str, Any] = {}           # 元素属性
    is_visible: bool = True                   # 是否可见
    xpaths: Optional[List[str]] = None        # XPath 路径
    
    async def tap(self) -> None:
        """点击元素"""
        raise NotImplementedError
    
    async def input_text(self, text: str) -> None:
        """向元素输入文本"""
        raise NotImplementedError
```

#### NodeType (节点类型)
```python
class NodeType(str, Enum):
    """UI 节点类型枚举"""
    CONTAINER = "container"  # 容器元素
    TEXT = "text"           # 文本元素
    INPUT = "input"         # 输入元素
    BUTTON = "button"       # 按钮元素
    IMAGE = "image"         # 图像元素
    LINK = "link"          # 链接元素
    OTHER = "other"        # 其他元素

# 使用示例
login_button = BaseElement(
    id="login-btn",
    content="登录",
    rect=Rect(100, 200, 80, 32),
    center=(140, 216),
    node_type=NodeType.BUTTON,
    attributes={"class": "btn btn-primary", "type": "submit"}
)
```

### UI 树形结构

#### UINode (UI 节点)
```python
class UINode(BaseModel):
    """UI 树节点表示"""
    id: str                                # 节点 ID
    content: str                          # 节点内容
    rect: Rect                            # 节点区域
    center: tuple[float, float]           # 节点中心
    node_type: NodeType                   # 节点类型
    attributes: Dict[str, Any] = {}       # 节点属性
    is_visible: bool = True               # 是否可见
    children: List['UINode'] = []         # 子节点列表

# 使用示例
form_node = UINode(
    id="login-form",
    content="登录表单",
    rect=Rect(50, 100, 300, 200),
    center=(200, 200),
    node_type=NodeType.CONTAINER,
    children=[
        UINode(id="username-input", content="用户名", ...),
        UINode(id="password-input", content="密码", ...),
        UINode(id="submit-btn", content="登录", ...)
    ]
)
```

#### UITree (UI 树)
```python
class UITree(BaseModel):
    """UI 树表示"""
    node: UINode                    # 根节点
    children: List['UITree'] = []   # 子树列表

# 构建 UI 树
page_tree = UITree(
    node=UINode(id="root", content="页面根节点", ...),
    children=[
        UITree(node=UINode(id="header", content="页面头部", ...)),
        UITree(node=UINode(id="main", content="主要内容", ...)),
        UITree(node=UINode(id="footer", content="页面底部", ...))
    ]
)
```

### UI 上下文

#### UIContext (UI 上下文)
```python
class UIContext(BaseModel, Generic[ElementType]):
    """UI 上下文包含截图和元素信息"""
    screenshot_base64: str          # Base64 编码的截图
    size: Size                     # 视口大小
    content: List[ElementType]     # 页面元素列表
    tree: UITree                   # UI 树结构

# 使用示例
context = UIContext[BaseElement](
    screenshot_base64="iVBORw0KGgoAAAANSUhEUgAA...",
    size=Size(width=1920, height=1080),
    content=[login_button, username_input, password_input],
    tree=page_tree
)

# 访问上下文信息
screenshot_data = base64.b64decode(context.screenshot_base64)
viewport_width = context.size.width
all_buttons = [elem for elem in context.content if elem.node_type == NodeType.BUTTON]
```

## 🔄 结果数据模型

### 执行结果

#### ExecutionResult (执行结果)
```python
class ExecutionResult(BaseModel, Generic[T]):
    """通用执行结果"""
    success: bool = True                    # 是否成功
    data: Optional[Any] = None             # 结果数据
    error: Optional[str] = None            # 错误信息
    usage: Optional[AIUsageInfo] = None    # AI 使用统计

# 使用示例
def process_action() -> ExecutionResult[Dict[str, str]]:
    try:
        result_data = {"user_id": "123", "username": "admin"}
        return ExecutionResult(
            success=True,
            data=result_data,
            usage=AIUsageInfo(total_tokens=150)
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            error=str(e)
        )
```

#### LocateResult (定位结果)
```python
class LocateResult(BaseModel):
    """元素定位结果"""
    element: Optional[BaseElement] = None   # 找到的元素
    rect: Optional[Rect] = None            # 元素区域

# 使用示例
locate_result = LocateResult(
    element=login_button,
    rect=login_button.rect
)

if locate_result.element:
    await locate_result.element.tap()
```

#### AssertResult (断言结果)
```python
class AssertResult(BaseModel):
    """断言结果"""
    passed: bool           # 断言是否通过
    thought: str = ""      # AI 推理过程
    message: str = ""      # 详细消息

# 使用示例
assert_result = AssertResult(
    passed=True,
    thought="页面显示了用户头像和用户名，表明登录成功",
    message="用户成功登录验证通过"
)
```

### AI 使用统计

#### AIUsageInfo (AI 使用信息)
```python
class AIUsageInfo(BaseModel):
    """AI 使用统计信息"""
    prompt_tokens: int = 0             # 输入 token 数量
    completion_tokens: int = 0         # 输出 token 数量
    total_tokens: int = 0             # 总 token 数量
    cost: Optional[float] = None      # 费用（如果可计算）

# 使用示例
usage = AIUsageInfo(
    prompt_tokens=1200,
    completion_tokens=300,
    total_tokens=1500,
    cost=0.045  # 美元
)

print(f"本次调用费用: ${usage.cost:.3f}")
print(f"Token 使用效率: {usage.completion_tokens/usage.prompt_tokens:.2f}")
```

## 🔧 配置数据模型

### Agent 配置

#### AgentOptions (Agent 配置选项)
```python
@dataclass
class AgentOptions:
    """Agent 配置选项"""
    test_id: Optional[str] = None           # 测试 ID
    cache_id: Optional[str] = None          # 缓存 ID
    group_name: str = "Midscene Report"     # 报告分组名称
    timeout: int = 30                       # 超时时间
    retry_count: int = 3                    # 重试次数
    screenshot_on_error: bool = True        # 错误时截图
    cache_enabled: bool = True              # 启用缓存

# 使用示例
options = AgentOptions(
    test_id="login_test_001",
    timeout=60,
    retry_count=5,
    group_name="登录测试套件"
)
```

### 操作选项

#### LocateOption (定位选项)
```python
@dataclass
class LocateOption:
    """元素定位选项"""
    multiple: bool = False                  # 查找多个元素
    timeout: int = 10                       # 定位超时
    wait_for_visible: bool = True           # 等待可见
    confidence_threshold: float = 0.8       # 置信度阈值

# 使用示例
locate_options = LocateOption(
    multiple=True,
    timeout=15,
    confidence_threshold=0.9
)
```

#### ExtractOption (提取选项)
```python
@dataclass  
class ExtractOption:
    """数据提取选项"""
    return_thought: bool = False            # 返回推理过程
    schema_validation: bool = True          # 模式验证
    timeout: int = 30                       # 提取超时

# 使用示例
extract_options = ExtractOption(
    return_thought=True,
    timeout=45
)
```

## 🔍 抽象接口

### 平台抽象接口

#### AbstractInterface (抽象接口)
```python
class AbstractInterface(ABC):
    """平台实现的抽象接口"""
    
    @property
    @abstractmethod
    def interface_type(self) -> InterfaceType:
        """获取接口类型"""
        pass
    
    @abstractmethod
    async def get_context(self) -> UIContext:
        """获取当前 UI 上下文"""
        pass
    
    @abstractmethod
    async def action_space(self) -> List[str]:
        """获取可用操作列表"""
        pass
    
    @abstractmethod
    async def tap(self, x: float, y: float) -> None:
        """在坐标处点击"""
        pass
    
    @abstractmethod
    async def input_text(self, text: str) -> None:
        """输入文本"""
        pass
    
    @abstractmethod
    async def scroll(self, direction: str, distance: Optional[int] = None) -> None:
        """滚动操作"""
        pass
```

#### InterfaceType (接口类型)
```python
class InterfaceType(str, Enum):
    """接口类型枚举"""
    WEB = "web"        # Web 平台
    ANDROID = "android" # Android 平台

# 平台实现示例
class WebInterface(AbstractInterface):
    @property
    def interface_type(self) -> InterfaceType:
        return InterfaceType.WEB
    
    async def get_context(self) -> UIContext:
        # 实现 Web 平台的上下文获取
        pass
```

## 📝 类型别名和泛型

### 类型别名
```python
# 用户提示类型
TUserPrompt = Union[str, Dict[str, Any]]

# 元素查找函数类型
ElementById = Callable[[str], Optional[BaseElement]]

# 任务开始提示函数类型
OnTaskStartTip = Callable[[str], Union[None, Awaitable[None]]]

# 使用示例
async def process_prompt(prompt: TUserPrompt) -> str:
    if isinstance(prompt, str):
        return prompt
    else:
        return prompt.get("text", "")
```

### 泛型支持
```python
# 泛型类型变量
ElementType = TypeVar('ElementType', bound='BaseElement')
T = TypeVar('T')

# 泛型类使用
class TypedUIContext(UIContext[ElementType]):
    """类型化的 UI 上下文"""
    
    def get_elements_by_type(self, node_type: NodeType) -> List[ElementType]:
        return [elem for elem in self.content if elem.node_type == node_type]

# 具体类型实例化
web_context: TypedUIContext[WebElement] = get_web_context()
android_context: TypedUIContext[AndroidElement] = get_android_context()
```

## 🎨 数据验证和序列化

### Pydantic 验证
```python
from pydantic import BaseModel, validator, Field

class ValidatedElement(BaseModel):
    """带验证的元素类"""
    id: str = Field(..., min_length=1, description="元素 ID 不能为空")
    content: str = Field(default="", description="元素内容")
    rect: Rect = Field(..., description="元素矩形区域")
    
    @validator('rect')
    def validate_rect(cls, v):
        if v.width < 0 or v.height < 0:
            raise ValueError("矩形的宽度和高度必须为正数")
        return v
    
    @validator('id')
    def validate_id(cls, v):
        if not v.strip():
            raise ValueError("元素 ID 不能为空字符串")
        return v.strip()

# 使用验证
try:
    element = ValidatedElement(
        id="  login-btn  ",  # 自动去除空格
        rect=Rect(100, 200, 80, 32)
    )
    print(element.id)  # "login-btn"
except ValueError as e:
    print(f"验证失败: {e}")
```

### JSON 序列化
```python
# 序列化到 JSON
context_json = context.json()
element_dict = element.dict()

# 从 JSON 反序列化
context_from_json = UIContext.parse_raw(context_json)
element_from_dict = BaseElement(**element_dict)

# 自定义序列化
class CustomElement(BaseElement):
    class Config:
        # 排除某些字段
        fields = {"internal_data": {"exclude": True}}
        
        # 自定义字段别名
        field_alias_generator = lambda field_name: field_name.replace("_", "-")
        
        # JSON 编码器
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

## 🔄 数据流和上下文传递

### 上下文提供者模式
```python
from typing import Union, Callable, Awaitable

# 静态上下文
static_context = UIContext(...)

# 动态上下文函数
async def dynamic_context_provider(action: InsightAction) -> UIContext:
    if action == InsightAction.LOCATE:
        return await get_locate_context()
    elif action == InsightAction.EXTRACT:
        return await get_extract_context()
    else:
        return await get_default_context()

# 上下文提供者类型
ContextProvider = Union[
    UIContext,
    Callable[[InsightAction], Union[UIContext, Awaitable[UIContext]]]
]

# 使用上下文提供者
class SmartContextProvider:
    def __init__(self):
        self.cache = {}
    
    async def __call__(self, action: InsightAction) -> UIContext:
        cache_key = f"{action}_{hash(time.time() // 60)}"  # 每分钟更新
        
        if cache_key not in self.cache:
            self.cache[cache_key] = await self._fetch_context(action)
        
        return self.cache[cache_key]
    
    async def _fetch_context(self, action: InsightAction) -> UIContext:
        # 根据操作类型获取优化的上下文
        pass
```

### 数据转换和适配
```python
class DataAdapter:
    """数据适配器，处理不同平台间的数据转换"""
    
    @staticmethod
    def web_element_to_base(web_element: WebElement) -> BaseElement:
        """Web 元素转换为基础元素"""
        return BaseElement(
            id=web_element.get_attribute("id") or web_element.tag_name,
            content=web_element.text,
            rect=Rect(*web_element.rect),
            center=(web_element.location['x'], web_element.location['y']),
            node_type=DataAdapter._infer_node_type(web_element),
            attributes=web_element.get_attributes()
        )
    
    @staticmethod
    def android_element_to_base(android_element: AndroidElement) -> BaseElement:
        """Android 元素转换为基础元素"""
        bounds = android_element.bounds
        return BaseElement(
            id=android_element.resource_id or android_element.class_name,
            content=android_element.text or android_element.content_desc,
            rect=Rect(bounds[0], bounds[1], bounds[2]-bounds[0], bounds[3]-bounds[1]),
            center=((bounds[0]+bounds[2])/2, (bounds[1]+bounds[3])/2),
            node_type=DataAdapter._infer_node_type_android(android_element),
            attributes=android_element.get_attributes()
        )
    
    @staticmethod
    def _infer_node_type(element) -> NodeType:
        """推断元素类型"""
        tag_name = element.tag_name.lower()
        
        if tag_name in ['button', 'input[type="button"]', 'input[type="submit"]']:
            return NodeType.BUTTON
        elif tag_name in ['input', 'textarea']:
            return NodeType.INPUT
        elif tag_name in ['img']:
            return NodeType.IMAGE
        elif tag_name in ['a']:
            return NodeType.LINK
        elif tag_name in ['div', 'section', 'article']:
            return NodeType.CONTAINER
        else:
            return NodeType.OTHER
```

## 🎯 最佳实践

### 1. 类型安全使用
```python
# ✅ 使用类型注解
async def process_elements(elements: List[BaseElement]) -> Dict[str, int]:
    type_counts: Dict[str, int] = {}
    for element in elements:
        type_name = element.node_type.value
        type_counts[type_name] = type_counts.get(type_name, 0) + 1
    return type_counts

# ✅ 使用 Optional 处理可能为空的值
def get_element_text(element: Optional[BaseElement]) -> str:
    return element.content if element else ""
```

### 2. 数据验证
```python
# ✅ 在数据边界进行验证
def create_safe_element(data: Dict[str, Any]) -> BaseElement:
    # 数据清理和验证
    data = {k: v for k, v in data.items() if v is not None}
    
    # 使用 Pydantic 验证
    return BaseElement(**data)

# ✅ 自定义验证器
class StrictElement(BaseElement):
    @validator('rect')
    def rect_must_be_positive(cls, v):
        if v.width <= 0 or v.height <= 0:
            raise ValueError('元素尺寸必须为正数')
        return v
```

### 3. 上下文管理
```python
# ✅ 合理的上下文缓存
class ContextManager:
    def __init__(self, ttl: int = 30):
        self.cache = {}
        self.ttl = ttl
    
    async def get_context(self, action: InsightAction) -> UIContext:
        now = time.time()
        cache_key = action.value
        
        if (cache_key in self.cache and 
            now - self.cache[cache_key]['timestamp'] < self.ttl):
            return self.cache[cache_key]['context']
        
        context = await self._fetch_fresh_context(action)
        self.cache[cache_key] = {
            'context': context,
            'timestamp': now
        }
        return context
```

### 4. 错误处理
```python
# ✅ 优雅的错误处理
async def safe_element_operation(element: Optional[BaseElement]) -> ExecutionResult:
    try:
        if not element:
            return ExecutionResult(
                success=False,
                error="元素为空"
            )
        
        await element.tap()
        return ExecutionResult(success=True)
        
    except NotImplementedError:
        return ExecutionResult(
            success=False,
            error="该平台不支持此操作"
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            error=f"操作失败: {str(e)}"
        )
```

## 🔗 相关文档

- **Agent 使用**: [Agent 核心控制器](Agent核心控制器.md)
- **Insight 引擎**: [Insight UI理解引擎](Insight-UI理解引擎.md)
- **平台集成**: [Web自动化](../平台集成/Web自动化/README.md) | [Android自动化](../平台集成/Android自动化.md)
- **API 参考**: [Agent API](../API参考/Agent-API.md)

---

理解 UI上下文与数据模型是掌握 Midscene Python 的关键。这些类型系统不仅保证了代码的可靠性，还为跨平台的一致性操作提供了基础！