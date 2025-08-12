# Component Factory Implementation

## How Dynamic Component Creation Works

This document explains the **Component Factory pattern** implementation in the French News Scraper - how components are created dynamically from configuration strings.

## Factory Pattern in Action

### **Problem Being Solved**
- Need to create different scrapers and parsers based on configuration
- Want to add new sources without modifying main pipeline code
- Need to support testing with mock components

### **Solution Architecture**
```
Configuration → ComponentFactory → create_component() → import_class() → Instance
```

## Code Flow Deep Dive

### 1. **Configuration Defines Component Classes** (`config/source_configs.py`)

```python
{
    "name": "Slate.fr",
    "scraper_class": "scrapers.slate_fr_scraper.SlateFrURLScraper",
    "parser_class": "parsers.database_slate_fr_parser.DatabaseSlateFrParser",
    "scraper_kwargs": {"debug": DEBUG}
}
```

**Key Points:**
- Classes specified as **strings**, not imports
- Allows configuration-driven component selection
- `scraper_kwargs` provides constructor arguments

### 2. **Factory Orchestrates Creation** (`core/component_factory.py`)

```python
class ComponentFactory:
    def create_scraper(self, config: dict) -> Any:
        return create_component(
            config["scraper_class"], 
            **(config.get("scraper_kwargs", {}))
        )
    
    def create_parser(self, config: dict, source_id: str) -> Any:
        parser_class_path = config.get("parser_class")
        parser_kwargs = config.get("parser_kwargs", {})
        return create_component(parser_class_path, source_id, **parser_kwargs)
```

**Factory Responsibilities:**
- **Extract** class path from configuration
- **Extract** constructor arguments from configuration  
- **Delegate** to lower-level component creation
- **Handle** missing configuration gracefully

### 3. **Dynamic Class Loading** (`core/component_loader.py`)

```python
def create_component(class_path: str, *args, **kwargs) -> Any:
    component_class = import_class(class_path)  # Get class object
    return component_class(*args, **kwargs)     # Instantiate with arguments

def import_class(class_path: str):
    # Split "scrapers.slate_fr_scraper.SlateFrURLScraper" 
    module_path, class_name = class_path.rsplit('.', 1)
    
    # Import module: scrapers.slate_fr_scraper
    module = importlib.import_module(module_path)
    
    # Get class: SlateFrURLScraper  
    return getattr(module, class_name)
```

**Dynamic Loading Process:**
1. **Parse** class path string into module + class name
2. **Import** module using Python's `importlib`
3. **Extract** class object using `getattr()`
4. **Return** class (not instance) for instantiation

## Execution Trace Example

When processing Slate.fr articles:

### **Step 1: Configuration Lookup**
```python
# article_pipeline.py:124
scraper = self.component_factory.create_scraper(config)

# config contains:
{
    "scraper_class": "scrapers.slate_fr_scraper.SlateFrURLScraper",
    "scraper_kwargs": {"debug": True}
}
```

### **Step 2: Factory Method Call**
```python
# component_factory.py:15-20
def create_scraper(self, config):
    return create_component(
        "scrapers.slate_fr_scraper.SlateFrURLScraper",  # class_path
        debug=True                                       # **scraper_kwargs
    )
```

### **Step 3: Component Creation**
```python
# component_loader.py:11-27
def create_component(class_path, debug=True):
    component_class = import_class("scrapers.slate_fr_scraper.SlateFrURLScraper")
    return component_class(debug=True)  # Call SlateFrURLScraper(debug=True)
```

### **Step 4: Dynamic Import**
```python
# component_loader.py:30-52
def import_class("scrapers.slate_fr_scraper.SlateFrURLScraper"):
    module_path = "scrapers.slate_fr_scraper"
    class_name = "SlateFrURLScraper"
    
    module = importlib.import_module("scrapers.slate_fr_scraper")
    return getattr(module, "SlateFrURLScraper")  # Returns class object
```

### **Step 5: Instance Creation**
```python
# Back in create_component():
SlateFrURLScraper = import_class(...)           # Class object
return SlateFrURLScraper(debug=True)            # Instance with arguments
```

## Error Handling Strategy

### **Import Errors** (`component_loader.py:48-52`)
```python
try:
    module = importlib.import_module(module_path)
    return getattr(module, class_name)
except (ImportError, AttributeError) as e:
    raise ImportError(f"Failed to import {class_path}: {e}")
```

### **Configuration Errors** (`component_factory.py:24-26`)
```python
if not parser_class_path:
    raise ValueError(f"No parser_class specified in config for source: {config['name']}")
```

### **Factory Error Propagation** (`article_pipeline.py:134-141`)
```python
try:
    scraper = self.component_factory.create_scraper(config)
    database_parser = self.component_factory.create_parser(config, source_id)
except (ValueError, ImportError) as e:
    self.output.error("Component initialization failed", extra_data={"error": str(e)})
    return 0, 0  # Skip this source, continue with others
```

## Benefits of This Pattern

### **Configuration-Driven Architecture**
- **Add new sources** by editing configuration only
- **No code changes** in main pipeline logic
- **Easy A/B testing** by switching component implementations

### **Testability**
```python
# Easy to inject test components
test_config = {
    "scraper_class": "tests.fixtures.mock_scraper.MockScraper",
    "parser_class": "tests.fixtures.mock_parser.MockParser"
}
```

### **Separation of Concerns**
- **ComponentFactory**: Knows about configuration structure
- **create_component()**: Knows about dynamic instantiation
- **import_class()**: Knows about Python import system
- **DatabaseProcessor**: Knows about business logic only

## Alternative Implementations

### **Direct Imports (Simpler)**
```python
# Instead of factory:
if config["name"] == "Slate.fr":
    from scrapers.slate_fr_scraper import SlateFrURLScraper
    scraper = SlateFrURLScraper(debug=DEBUG)
elif config["name"] == "FranceInfo.fr":
    from scrapers.france_info_scraper import FranceInfoURLScraper
    scraper = FranceInfoURLScraper(debug=DEBUG)
```

**Trade-offs:**
- ✅ **Simpler**: No factory complexity
- ✅ **Faster**: No dynamic imports
- ❌ **Less flexible**: Hard-coded component selection
- ❌ **More maintenance**: New sources require code changes

### **Registry Pattern (More Complex)**
```python
# Component registry with automatic discovery
SCRAPER_REGISTRY = {
    "Slate.fr": SlateFrURLScraper,
    "FranceInfo.fr": FranceInfoURLScraper
}

scraper = SCRAPER_REGISTRY[config["name"]](debug=DEBUG)
```

**Trade-offs:**
- ✅ **Fast lookups**: No import overhead
- ✅ **Type safe**: Direct class references
- ❌ **Manual registration**: Must maintain registry
- ❌ **Import overhead**: All classes loaded at startup

## When to Use Factory Pattern

### **Good Use Cases** ✅
- Multiple implementations of same interface
- Component selection based on runtime configuration
- Need to support plugin architectures
- Testing requires component substitution

### **Avoid When** ❌
- Only one implementation exists
- Component selection is compile-time decision
- Performance is critical (dynamic imports have overhead)
- Code base is small and stable

## Performance Considerations

### **Import Cost**
- **First import**: ~1-5ms per module (file I/O, parsing)
- **Subsequent imports**: ~0.1ms (cached in `sys.modules`)
- **Memory**: Each imported module stays in memory

### **Optimization Strategies**
```python
# Cache imported classes to avoid repeated imports
_CLASS_CACHE = {}

def import_class_cached(class_path: str):
    if class_path not in _CLASS_CACHE:
        _CLASS_CACHE[class_path] = import_class(class_path)
    return _CLASS_CACHE[class_path]
```

This factory implementation provides flexibility for adding new news sources while maintaining clean separation between configuration and business logic.