"""
干员生日
ref:
https://prts.wiki/index.php?title=%E5%B1%9E%E6%80%A7:%E7%94%9F%E6%97%A5&limit=10000&offset=0&from=&until=&filter=
在上面链接的页面中，打开浏览器控制台，粘贴以下代码并回车，即可获取所有干员的生日信息，并以JSON格式输出

// 获取所有符合条件的行元素
const rows = document.querySelectorAll('.smw-table-row.value-row');

// 存储结果的数组
const results = [];

// 遍历每一行
rows.forEach(row => {
	// 获取干员名字（在第一个 smw-table-cell 中的 a 标签）
	const nameCell = row.querySelector('.smw-table-cell.smwpropname a');
	const name = nameCell ? nameCell.textContent.trim() : null;
	
	// 获取生日信息（在第二个 smw-table-cell 中，直接取文本节点）
	const birthdayCell = row.querySelector('.smw-table-cell.smwprops');
	let birthday = null;
	
	if (birthdayCell) {
		// 直接获取第一个文本节点的内容
		const textNode = Array.from(birthdayCell.childNodes).find(node => node.nodeType === 3);
		birthday = textNode ? textNode.textContent.trim() : null;
	}
	
	// 如果名字存在，则添加到结果中
	if (name) {
		results.push({
			name: name,
			birthday: birthday || '未知'
		});
	}
});

// 输出JSON格式
const jsonString = JSON.stringify(results, null, 2);
console.log(jsonString);
console.log(`\n成功提取 ${results.length} 条数据`);
"""

import os
import json

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class Birthday:
    """
    加载和查询干员生日信息
    """

    def __init__(self, path: str = "rmts/resources/json/birthday/birthday.json") -> None:
        """
        初始化
        """

        # 使用相对于当前文件的路径
        current_dir = Path(__file__).parent.parent.parent.parent.parent
        self.path = current_dir / "resources" / "json" / "birthday" / "birthday.json"
        self.data = self.load_data()

    def load_data(self) -> List[Dict[str, str]]:
        """
        加载数据
        """

        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data
    
    def get_birth_by_date(self, date: str) -> Optional[List[str]]:
        """
        通过日期获取过生日的干员
        Args:
            date: 日期字符串，格式为 "MM月DD日"，例如 "1月1日"
        """

        result = [item["name"] for item in self.data if item["birthday"] == date]
        return result if result else None

    def get_birth_today(self) -> Optional[List[str]]:
        """
        获取今天过生日的干员
        """

        now = datetime.now()
        date_str = f"{now.month}月{now.day}日"
        return self.get_birth_by_date(date_str)
    
    def get_birth_by_name(self, name: str) -> Optional[str]:
        """
        通过名字获取干员的生日
        Args:
            name: 干员名字
        """

        for item in self.data:
            if item["name"] == name:
                return item["birthday"]
        
        return None

if __name__ == "__main__":
    birthday = Birthday()
    print(birthday.get_birth_by_date("3月15日"))
    print(birthday.get_birth_today())
    print(birthday.get_birth_by_name("迷迭香"))
