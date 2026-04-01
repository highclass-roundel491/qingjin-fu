# 青衿赋 - API接口文档

## 1. 接口规范

### 1.1 基础信息
- Base URL: `http://localhost:8000/api/v1`
- 协议: HTTP/HTTPS
- 数据格式: JSON
- 字符编码: UTF-8

### 1.2 通用响应格式
```json
{
    "code": 200,
    "message": "success",
    "data": {}
}
```

### 1.3 错误码定义
| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

### 1.4 认证方式
```
Authorization: Bearer {access_token}
```

## 2. 用户模块

### 2.1 用户注册

**POST** `/users/register`

请求体:
```json
{
    "username": "string",
    "email": "string",
    "password": "string",
    "phone": "string"
}
```

响应:
```json
{
    "code": 201,
    "message": "注册成功",
    "data": {
        "user_id": 1,
        "username": "string",
        "email": "string"
    }
}
```

### 2.2 用户登录

**POST** `/users/login`

请求体:
```json
{
    "username": "string",
    "password": "string"
}
```

响应:
```json
{
    "code": 200,
    "message": "登录成功",
    "data": {
        "access_token": "string",
        "refresh_token": "string",
        "token_type": "bearer",
        "expires_in": 7200
    }
}
```

### 2.3 获取当前用户信息

**GET** `/users/me`

响应:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "username": "string",
        "email": "string",
        "phone": "string",
        "nickname": "string",
        "avatar_url": "string",
        "bio": "string",
        "level": 1,
        "exp": 0,
        "points": 0,
        "is_active": true,
        "created_at": "2026-03-07T00:00:00Z"
    }
}
```

### 2.4 更新用户信息

**PUT** `/users/me`

请求体:
```json
{
    "nickname": "string",
    "avatar_url": "string",
    "bio": "string"
}
```

响应:
```json
{
    "code": 200,
    "message": "用户信息更新成功",
    "data": {
        "id": 1,
        "username": "string",
        "nickname": "string",
        "avatar_url": "string",
        "bio": "string"
    }
}
```

### 2.5 修改密码

**POST** `/users/change-password`

请求体:
```json
{
    "old_password": "string",
    "new_password": "string"
}
```

响应:
```json
{
    "code": 200,
    "message": "密码修改成功"
}
```

### 2.6 获取当前用户收藏列表

**GET** `/users/me/favorites?page=1&page_size=20`

查询参数:
- page: 页码（默认1）
- page_size: 每页数量（默认20，最大100）

响应:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [
            {
                "id": 1,
                "title": "静夜思",
                "author": "李白",
                "dynasty": "唐",
                "content": "床前明月光...",
                "category": "思乡",
                "genre": "五言绝句",
                "view_count": 100,
                "favorite_count": 50
            }
        ],
        "total": 100,
        "page": 1,
        "page_size": 20
    }
}
```

### 2.7 上传头像

**POST** `/users/me/avatar`

请求方式: `multipart/form-data`

字段:
- file: 图片文件（支持 jpg/jpeg/png/gif/webp，最大 2MB）

响应:
```json
{
    "code": 200,
    "message": "头像上传成功",
    "data": {
        "avatar_url": "/uploads/avatars/1_a1b2c3d4.jpg"
    }
}
```

### 2.8 获取经验获取历史

**GET** `/users/me/exp-history?page=1&page_size=20`

查询参数:
- page: 页码（默认1）
- page_size: 每页数量（默认20，最大100）

响应:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [
            {
                "id": "challenge-1",
                "source": "challenge",
                "source_label": "妙笔挑战",
                "title": "填字妙想",
                "detail": "完成填字妙想，内容「春风拂柳绿」",
                "exp": 44,
                "occurred_at": "2026-03-07T10:00:00Z"
            },
            {
                "id": "learning-5",
                "source": "learning",
                "source_label": "诗词研习",
                "title": "首次有效研习",
                "detail": "研习《静夜思》",
                "exp": 5,
                "occurred_at": "2026-03-07T09:00:00Z"
            }
        ],
        "total": 50,
        "page": 1,
        "page_size": 20
    }
}
```

source 说明:
- challenge: 妙笔挑战
- learning: 诗词研习
- work: 作品创作
- achievement: 成就解锁
- relay: 诗词接龙
- feihualing: 飞花令

### 2.9 获取用户统计数据

**GET** `/users/{user_id}/stats`

响应:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "total_study_time": 3600,
        "total_poems_learned": 100,
        "total_questions_answered": 200,
        "correct_rate": 85.5,
        "total_works_created": 50,
        "total_likes_received": 300,
        "follower_count": 0,
        "following_count": 0
    }
}
```

## 3. 诗词模块

### 3.1 搜索诗词

**GET** `/poems/search?keyword=明月&search_type=content&page=1&page_size=20`

查询参数:
- keyword: 搜索关键词（必填）
- search_type: 搜索类型（title/author/content，默认content）
- page: 页码
- page_size: 每页数量

响应:
```json
{
    "items": [
        {
            "id": 1,
            "title": "静夜思",
            "author": "李白",
            "dynasty": "唐",
            "content": "床前明月光...",
            "category": "思乡",
            "genre": "五言绝句",
            "view_count": 100,
            "favorite_count": 50
        }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
}
```

### 3.2 获取诗词列表

**GET** `/poems?page=1&page_size=20&dynasty=唐&author=李白&search=明月`

查询参数:
- page: 页码
- page_size: 每页数量
- dynasty: 朝代筛选
- author: 作者筛选
- search: 搜索关键词（标题/作者/内容）

响应:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [
            {
                "id": 1,
                "title": "静夜思",
                "author": "李白",
                "dynasty": "唐",
                "content": "床前明月光...",
                "category": "思乡",
                "genre": "五言绝句",
                "view_count": 100,
                "favorite_count": 50
            }
        ],
        "total": 100,
        "page": 1,
        "page_size": 20
    }
}
```

### 3.2 获取诗词详情

**GET** `/poems/{poem_id}`

响应:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "title": "静夜思",
        "author": "李白",
        "dynasty": "唐",
        "content": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
        "translation": "明亮的月光洒在床前...",
        "annotation": "床：井栏...",
        "background": "创作于唐玄宗开元十四年...",
        "appreciation": "这首诗表达了诗人的思乡之情...",
        "category": "思乡",
        "genre": "五言绝句",
        "tags": ["思乡", "月亮"],
        "view_count": 100,
        "favorite_count": 50,
        "is_favorited": false
    }
}
```

### 3.3 随机获取诗词

**GET** `/poems/random?count=1`

查询参数:
- count: 返回数量（默认1）

### 3.4 增加浏览量

**POST** `/poems/{poem_id}/view`

说明: 每次查看诗词详情时调用，用于统计浏览量，使用内存计数器批量写入。

响应:
```json
{
    "message": "浏览量已更新"
}
```

### 3.5 收藏诗词

**POST** `/poems/{poem_id}/favorite`

响应:
```json
{
    "code": 200,
    "message": "收藏成功"
}
```

### 3.6 取消收藏

**DELETE** `/poems/{poem_id}/favorite`

响应:
```json
{
    "code": 200,
    "message": "取消收藏成功"
}
```

## 4. 每日挑战模块

### 4.1 获取每日挑战

**GET** `/challenges/daily`

说明: 获取当日的精选挑战题，每日自动更换。若未生成则返回 404。

响应:
```json
{
    "id": 1,
    "challenge_type": "fill_blank",
    "creator_id": null,
    "creator_name": null,
    "is_daily": true,
    "date": "2026-03-07",
    "sentence_template": "春风_柳绿",
    "sentence_template_2": "桃花_日红",
    "blank_count": 1,
    "theme": "春",
    "mood": "欢快",
    "hint": "填入动词",
    "difficulty": "medium",
    "status": "active",
    "original_answer": "拂",
    "original_answer_2": "映",
    "response_count": 15,
    "created_at": "2026-03-07T00:00:00Z"
}
```

### 4.2 获取挑战详情

**GET** `/challenges/{challenge_id}`

响应: 同 4.1 格式

### 4.3 获取挑战列表

**GET** `/challenges/list?challenge_type=fill_blank&page=1&page_size=20`

查询参数:
- challenge_type: 挑战类型（fill_blank/continue_line，可选）
- page: 页码
- page_size: 每页数量

响应:
```json
{
    "items": [
        {
            "id": 1,
            "challenge_type": "fill_blank",
            "creator_id": 1,
            "creator_name": "诗人",
            "is_daily": true,
            "date": "2026-03-07",
            "sentence_template": "春风_柳绿",
            "sentence_template_2": "桃花_日红",
            "blank_count": 1,
            "theme": "春",
            "mood": "欢快",
            "hint": "填入动词",
            "difficulty": "medium",
            "status": "active",
            "response_count": 15,
            "created_at": "2026-03-07T00:00:00Z"
        }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20
}
```

### 4.4 创建挑战

**POST** `/challenges/create`

请求体:
```json
{
    "challenge_type": "fill_blank",
    "sentence_template": "春风_柳绿",
    "sentence_template_2": "桃花_日红",
    "blank_count": 1,
    "original_answer": "拂",
    "original_answer_2": "映",
    "theme": "春",
    "mood": "欢快",
    "hint": "填入动词",
    "difficulty": "medium"
}
```

challenge_type 说明:
- fill_blank: 填字妙想（上下联各一个空）
- continue_line: 续写接力（给上句写下句）

响应: 同 4.1 格式

### 4.5 提交挑战答案

**POST** `/challenges/submit`

请求体:
```json
{
    "challenge_id": 1,
    "answer": "拂",
    "answer_2": "映",
    "content": "续写的完整内容"
}
```

响应:
```json
{
    "id": 1,
    "completed_sentence": "春风拂柳绿",
    "completed_sentence_2": "桃花映日红",
    "exp_gained": 44,
    "points_gained": 8,
    "ai_score": 88,
    "beauty_score": 85,
    "creativity_score": 90,
    "mood_score": 88,
    "ai_feedback": "评价内容",
    "ai_highlight": "亮点点评",
    "is_original_match": false
}
```

### 4.6 获取挑战历史

**GET** `/challenges/history?page=1&page_size=20`

查询参数:
- page: 页码
- page_size: 每页数量

响应:
```json
{
    "items": [
        {
            "id": 1,
            "challenge_id": 1,
            "answer": "拂",
            "answer_2": "映",
            "ai_score": 88,
            "ai_feedback": "评价内容",
            "beauty_score": 85,
            "creativity_score": 90,
            "mood_score": 88,
            "exp_gained": 44,
            "points_gained": 8,
            "submitted_at": "2026-03-07T10:00:00Z"
        }
    ],
    "total": 100,
    "streak_days": 5,
    "page": 1,
    "page_size": 20
}
```

### 4.7 删除提交记录

**DELETE** `/challenges/submissions/{submission_id}`

说明: 删除后会扣回对应的经验值和积分（防刷分机制）。

响应:
```json
{
    "id": 1,
    "exp_deducted": 44,
    "points_deducted": 8,
    "message": "已删除提交记录，相应经验与积分已扣回"
}
```

### 4.8 获取挑战排行榜

**GET** `/challenges/rankings?period=all&page=1&page_size=20`

查询参数:
- period: 周期（today/week/all）
- page: 页码
- page_size: 每页数量

响应:
```json
{
    "items": [
        {
            "rank": 1,
            "user_id": 1,
            "username": "诗人",
            "nickname": "妙笔生花",
            "avatar_url": null,
            "total_submissions": 50,
            "total_exp": 2200,
            "total_points": 400,
            "level": 5,
            "exp": 2200
        }
    ],
    "total": 100,
    "period": "all"
}
```

### 4.9 获取挑战作答列表

**GET** `/challenges/{challenge_id}/responses?page=1&page_size=20`

响应:
```json
{
    "items": [
        {
            "id": 1,
            "challenge_id": 1,
            "user_id": 1,
            "username": "诗人",
            "answer": "拂",
            "answer_2": "映",
            "content": null,
            "likes_count": 5,
            "submitted_at": "2026-03-07T10:00:00Z"
        }
    ],
    "total": 15,
    "page": 1,
    "page_size": 20
}
```

### 4.10 AI出题

**POST** `/challenges/ai-generate`

请求体:
```json
{
    "difficulty": "medium",
    "theme": "春",
    "dynasty": "唐"
}
```

响应:
```json
{
    "sentence_template": "春风_柳绿",
    "sentence_template_2": "桃花_日红",
    "blank_count": 1,
    "original_answer": "拂",
    "original_answer_2": "映",
    "theme": "春",
    "mood": "欢快",
    "hint": "填入动词",
    "difficulty": "medium",
    "poem_title": "嘉兴春望",
    "poem_author": "王维",
    "poem_dynasty": "唐"
}
```

### 4.11 AI提示

**POST** `/challenges/{challenge_id}/ai-hint`

请求体:
```json
{
    "hint_level": 1
}
```

hint_level: 1-3 级，逐级提示更明确

响应:
```json
{
    "hint_text": "这个字与微风有关...",
    "hint_level": 1,
    "next_available": true
}
```

### 4.12 AI作答赏析

**POST** `/challenges/{challenge_id}/ai-review`

响应:
```json
{
    "best_answer_index": 0,
    "best_reason": "意境深远，用字巧妙",
    "answer_tags": ["巧妙", "有意境"],
    "overall_review": "整体作答水平较高...",
    "diversity_note": "答案角度多样"
}
```

### 4.13 AI检查挑战题目

**POST** `/challenges/ai-check`

请求体:
```json
{
    "sentence_template": "春风_柳绿",
    "sentence_template_2": "桃花_日红",
    "user_answer": "拂"
}
```

响应:
```json
{
    "is_valid": true,
    "feedback": "题目格式正确，韵律合理",
    "suggestions": []
}
```

## 5. 学习进度模块

### 5.1 记录学习行为

**POST** `/learning/record`

请求体:
```json
{
    "poem_id": 1,
    "action": "view",
    "duration": 120
}
```

响应:
```json
{
    "message": "学习记录已保存"
}
```

### 5.2 获取学习统计

**GET** `/learning/stats`

响应:
```json
{
    "total_learned": 100,
    "total_favorites": 50,
    "study_time": 3600,
    "streak_days": 5,
    "level": 3,
    "exp": 1500,
    "next_level_exp": 1500
}
```

### 5.3 获取收藏列表

**GET** `/learning/favorites?page=1&page_size=20`

查询参数:
- page: 页码
- page_size: 每页数量

响应:
```json
{
    "items": [
        {
            "id": 1,
            "title": "静夜思",
            "author": "李白",
            "dynasty": "唐",
            "content": "床前明月光...",
            "category": "思乡",
            "genre": "五言绝句",
            "view_count": 100,
            "favorite_count": 50
        }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20
}
```

### 5.4 获取学习进度数据

**GET** `/learning/progress`

响应:
```json
{
    "daily_study_time": [
        {"date": "2026-03-01", "duration": 1800},
        {"date": "2026-03-02", "duration": 2400}
    ],
    "dynasty_distribution": [
        {"dynasty": "唐", "count": 50},
        {"dynasty": "宋", "count": 30}
    ],
    "genre_distribution": [
        {"genre": "五言绝句", "count": 20},
        {"genre": "七言律诗", "count": 15}
    ],
    "cumulative_learned": [
        {"date": "2026-03-01", "total": 50},
        {"date": "2026-03-02", "total": 52}
    ],
    "challenge_performance": {
        "beauty_avg": 85.5,
        "creativity_avg": 80.0,
        "mood_avg": 88.0
    },
    "study_calendar": [
        {"date": "2026-03-01", "activity": 3},
        {"date": "2026-03-02", "activity": 5}
    ]
}
```

## 6. 诗词创作模块

### 6.1 创建作品

**POST** `/works`

请求体:
```json
{
    "title": "春日即景",
    "content": "春风拂柳绿\n桃花映日红\n莺歌燕舞处\n诗意满园中",
    "genre": "五言绝句"
}
```

响应:
```json
{
    "code": 201,
    "message": "作品创建成功",
    "data": {
        "id": 1,
        "user_id": 1,
        "title": "春日即景",
        "content": "春风拂柳绿...",
        "genre": "五言绝句",
        "status": "draft",
        "created_at": "2026-03-07T10:00:00Z"
    }
}
```

### 6.2 更新作品

**PUT** `/works/{work_id}`

请求体:
```json
{
    "title": "春日即景",
    "content": "春风拂柳绿...",
    "genre": "五言绝句"
}
```

响应:
```json
{
    "code": 200,
    "message": "作品更新成功",
    "data": {
        "id": 1,
        "title": "春日即景",
        "content": "春风拂柳绿...",
        "genre": "五言绝句"
    }
}
```

### 6.3 发布作品

**POST** `/works/{work_id}/publish`

说明:
- 作品仅在首次发布时发放创作经验
- 单篇作品经验会根据体裁与内容长度计算，范围为 4~16 点
- 撤回后再次发布不会重复发放同一作品的创作经验
- 发布成功后会同步更新用户经验与等级

响应:
```json
{
    "code": 200,
    "message": "作品发布成功，获得13点经验",
    "data": {
        "id": 1,
        "status": "published",
        "published_at": "2026-03-07T10:00:00Z"
    }
}
```

### 6.4 撤回作品

**POST** `/works/{work_id}/unpublish`

响应:
```json
{
    "code": 200,
    "message": "作品已撤回至草稿",
    "data": {
        "id": 1,
        "status": "draft"
    }
}
```

### 6.5 删除作品

**DELETE** `/works/{work_id}`

响应:
```json
{
    "code": 200,
    "message": "作品已删除"
}
```

### 6.6 获取作品列表

**GET** `/works?sort=new&genre=五言绝句&page=1&page_size=20`

查询参数:
- sort: 排序方式（hot/new/score）
- genre: 体裁筛选
- page: 页码
- page_size: 每页数量

响应:
```json
{
    "code": 200,
    "data": {
        "items": [
            {
                "id": 1,
                "user_id": 1,
                "username": "诗人",
                "avatar_url": "https://...",
                "title": "春日即景",
                "content": "春风拂柳绿...",
                "genre": "五言绝句",
                "status": "published",
                "ai_total_score": 85,
                "like_count": 10,
                "view_count": 100,
                "is_liked": false,
                "created_at": "2026-03-07T10:00:00Z",
                "published_at": "2026-03-07T10:00:00Z"
            }
        ],
        "total": 100,
        "page": 1,
        "page_size": 20
    }
}
```

### 6.7 获取我的作品

**GET** `/works/mine?status=published&page=1&page_size=20`

查询参数:
- status: 状态筛选（draft/published）
- page: 页码
- page_size: 每页数量

响应格式同 6.6

### 6.8 获取作品详情

**GET** `/works/{work_id}`

响应:
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "user_id": 1,
        "username": "诗人",
        "avatar_url": "https://...",
        "title": "春日即景",
        "content": "春风拂柳绿...",
        "genre": "五言绝句",
        "status": "published",
        "ai_grammar_score": 85,
        "ai_artistic_score": 90,
        "ai_total_score": 88,
        "ai_feedback": "格律严谨，意境深远...",
        "like_count": 10,
        "view_count": 100,
        "is_liked": false,
        "created_at": "2026-03-07T10:00:00Z",
        "updated_at": "2026-03-07T10:00:00Z",
        "published_at": "2026-03-07T10:00:00Z"
    }
}
```

### 6.9 点赞作品

**POST** `/works/{work_id}/like`

响应:
```json
{
    "code": 200,
    "message": "点赞成功"
}
```

### 6.10 取消点赞

**DELETE** `/works/{work_id}/like`

响应:
```json
{
    "code": 200,
    "message": "取消点赞成功"
}
```

### 6.11 AI评分

**POST** `/works/{work_id}/ai-score`

响应:
```json
{
    "code": 200,
    "message": "AI评分完成",
    "data": {
        "work_id": 1,
        "grammar_score": 85,
        "artistic_score": 90,
        "total_score": 88,
        "feedback": "格律严谨，遣词用字工整；意境深远，文采斐然，颇具诗人气韵。",
        "composite_score": 87.5
    }
}
```

### 6.12 获取创作者排行榜

**GET** `/works/rankings?period=all&page=1&page_size=20`

查询参数:
- period: 周期（daily/weekly/all）
- page: 页码
- page_size: 每页数量

响应:
```json
{
    "code": 200,
    "data": {
        "items": [
            {
                "rank": 1,
                "user_id": 1,
                "username": "诗人",
                "avatar_url": "https://...",
                "work_count": 50,
                "total_likes": 500,
                "avg_score": 85.5
            }
        ],
        "total": 100
    }
}
```

### 6.13 获取作品排行榜

**GET** `/works/rankings/works?ranking_type=composite&period=all&genre=五言绝句&page=1&page_size=20`

查询参数:
- ranking_type: 排行类型（composite/ai_score/popularity）
- period: 周期（daily/weekly/monthly/all）
- genre: 体裁筛选
- page: 页码
- page_size: 每页数量

响应:
```json
{
    "code": 200,
    "data": {
        "items": [
            {
                "rank": 1,
                "work_id": 1,
                "title": "春日即景",
                "content": "春风拂柳绿...",
                "genre": "五言绝句",
                "user_id": 1,
                "username": "诗人",
                "avatar_url": "https://...",
                "like_count": 100,
                "view_count": 1000,
                "ai_grammar_score": 85,
                "ai_artistic_score": 90,
                "ai_total_score": 88,
                "composite_score": 87.5,
                "published_at": "2026-03-07T10:00:00Z"
            }
        ],
        "total": 100,
        "ranking_type": "composite",
        "period": "all"
    }
}
```

## 7. 诗词接龙模块

### 7.1 创建接龙房间

**POST** `/relay/rooms`

请求体:
```json
{
    "mode": "single",
    "difficulty": "normal",
    "max_rounds": 20,
    "time_limit": 30,
    "max_players": 2,
    "password": null
}
```

字段说明:
- mode: 游戏模式（single 单人练习 / multi 多人对战）
- difficulty: 难度（easy 简单 / normal 普通 / hard 困难）
- max_rounds: 最大回合数（默认20）
- time_limit: 每回合时间限制，秒（默认30）
- max_players: 最大人数（默认2）
- password: 房间密码（可选）

响应:
```json
{
    "code": 201,
    "message": "房间创建成功",
    "data": {
        "id": 1,
        "room_code": "ABCD1234",
        "mode": "single",
        "difficulty": "normal",
        "max_rounds": 20,
        "time_limit": 30,
        "status": "waiting",
        "host_id": 1,
        "host_username": "诗人",
        "created_at": "2026-03-08T10:00:00Z"
    }
}
```

### 7.2 获取房间大厅

**GET** `/relay/lobby?page=1&page_size=20`

查询参数:
- page: 页码
- page_size: 每页数量（最大50）

响应:
```json
{
    "items": [
        {
            "id": 1,
            "room_code": "ABCD1234",
            "difficulty": "normal",
            "max_rounds": 20,
            "time_limit": 30,
            "max_players": 2,
            "player_count": 1,
            "host_username": "诗人",
            "host_avatar": null,
            "has_password": false,
            "created_at": "2026-03-08T10:00:00Z"
        }
    ],
    "total": 5,
    "page": 1,
    "page_size": 20
}
```

### 7.3 快速匹配

**POST** `/relay/quick-match`

说明: 自动匹配一个等待中的多人房间，若无可用房间则自动创建新房间。

响应: 同 7.1 房间响应格式

### 7.4 加入接龙房间

**POST** `/relay/rooms/{room_code}/join?password=xxx`

查询参数:
- password: 房间密码（可选，仅当房间设置了密码时必填）

响应:
```json
{
    "code": 200,
    "message": "加入成功",
    "data": {
        "room_id": 1,
        "room_code": "ABCD1234",
        "players": [
            {
                "user_id": 1,
                "username": "诗人",
                "avatar_url": "https://...",
                "is_host": true
            }
        ]
    }
}
```

### 7.5 开始接龙游戏

**POST** `/relay/rooms/{room_id}/start`

响应:
```json
{
    "code": 200,
    "message": "游戏开始",
    "data": {
        "room_id": 1,
        "status": "playing",
        "current_round": 1,
        "starter_verse": "床前明月光",
        "starter_poem_title": "静夜思",
        "starter_author": "李白",
        "next_char": "光",
        "started_at": "2026-03-08T10:00:00Z"
    }
}
```

### 7.6 提交接龙诗句

**POST** `/relay/rooms/{room_id}/submit`

请求体:
```json
{
    "verse": "光阴似箭催人老"
}
```

响应:
```json
{
    "code": 200,
    "message": "接龙成功",
    "data": {
        "round": 2,
        "verse": "光阴似箭催人老",
        "poem_title": "劝学",
        "author": "颜真卿",
        "is_valid": true,
        "match_type": "exact",
        "score": 10,
        "next_char": "老",
        "time_used": 8,
        "combo": 2
    }
}
```

match_type 说明:
- exact: 完全匹配（尾字=首字）
- homophone: 同音匹配
- tone: 同韵匹配（仅困难模式不允许）

### 7.7 获取当前房间状态

**GET** `/relay/rooms/{room_id}`

响应:
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "room_code": "ABCD1234",
        "mode": "single",
        "difficulty": "normal",
        "status": "playing",
        "current_round": 5,
        "max_rounds": 20,
        "time_limit": 30,
        "next_char": "风",
        "players": [
            {
                "user_id": 1,
                "username": "诗人",
                "avatar_url": null,
                "score": 45,
                "combo": 3,
                "is_host": true
            }
        ],
        "rounds": [
            {
                "round": 1,
                "user_id": 0,
                "username": "系统",
                "verse": "床前明月光",
                "poem_title": "静夜思",
                "author": "李白",
                "score": 0,
                "time_used": 0
            },
            {
                "round": 2,
                "user_id": 1,
                "username": "诗人",
                "verse": "光阴似箭催人老",
                "poem_title": "劝学",
                "author": "颜真卿",
                "score": 10,
                "time_used": 8
            }
        ]
    }
}
```

### 7.8 获取提示

**GET** `/relay/rooms/{room_id}/hint`

响应:
```json
{
    "code": 200,
    "data": {
        "hints": [
            {
                "verse": "风吹柳花满店香",
                "poem_title": "金陵酒肆留别",
                "author": "李白"
            },
            {
                "verse": "风急天高猿啸哀",
                "poem_title": "登高",
                "author": "杜甫"
            }
        ],
        "hint_count_used": 1,
        "hint_count_max": 3
    }
}
```

### 7.9 结束游戏 / 认输

**POST** `/relay/rooms/{room_id}/end`

响应:
```json
{
    "code": 200,
    "message": "游戏结束",
    "data": {
        "room_id": 1,
        "total_rounds": 12,
        "duration": 360,
        "results": [
            {
                "user_id": 1,
                "username": "诗人",
                "total_score": 120,
                "max_combo": 5,
                "rounds_played": 12,
                "avg_time": 12.5,
                "rank": 1
            }
        ],
        "exp_gained": 60,
        "points_gained": 12,
        "new_achievements": []
    }
}
```

经验值计算规则:
- 每回合基础得分: 10 分
- 连击加成: min(combo - 1, 5) × 2 分（上限 +10）
- 最终经验: total_score ÷ 2（向下取整）
- 最终积分: total_score ÷ 10（向下取整）
- 经验累加后自动检测升级（等级阈值: 0/100/300/600/1000/1500/2200/3000）

等级对照表:
| 等级 | 称号 | 经验阈值 |
|------|------|----------|
| 1 | 童生 | 0 |
| 2 | 秀才 | 100 |
| 3 | 举人 | 300 |
| 4 | 贡士 | 600 |
| 5 | 进士 | 1000 |
| 6 | 探花 | 1500 |
| 7 | 榜眼 | 2200 |
| 8 | 状元 | 3000 |

### 7.10 获取接龙历史

**GET** `/relay/history?page=1&page_size=20`

查询参数:
- page: 页码
- page_size: 每页数量

响应:
```json
{
    "code": 200,
    "data": {
        "items": [
            {
                "room_id": 1,
                "mode": "single",
                "difficulty": "normal",
                "total_rounds": 12,
                "total_score": 120,
                "max_combo": 5,
                "duration": 360,
                "result": "completed",
                "played_at": "2026-03-08T10:00:00Z"
            }
        ],
        "total": 50,
        "page": 1,
        "page_size": 20
    }
}
```

### 7.11 获取接龙排行榜

**GET** `/relay/rankings?period=all&page=1&page_size=20`

查询参数:
- period: 周期（daily/weekly/all）
- page: 页码
- page_size: 每页数量

响应:
```json
{
    "code": 200,
    "data": {
        "items": [
            {
                "rank": 1,
                "user_id": 1,
                "username": "诗人",
                "avatar_url": null,
                "total_score": 1200,
                "total_games": 50,
                "max_combo": 15,
                "best_rounds": 25,
                "win_rate": 85.0
            }
        ],
        "total": 100,
        "period": "all"
    }
}
```

### 7.12 WebSocket 实时对战

**WebSocket** `ws://localhost:8000/api/v1/relay/ws/relay/{room_id}?token={access_token}`

说明: 多人接龙实时对战通信通道。连接时需携带 JWT Token 作为查询参数。

客户端发送消息格式:
```json
{
    "type": "submit",
    "verse": "光阴似箭催人老"
}
```

服务端推送消息类型:
- `player_joined`: 新玩家加入
- `game_started`: 游戏开始
- `verse_submitted`: 某玩家提交了诗句
- `game_ended`: 游戏结束
- `error`: 错误消息

## 8. 社交模块

### 8.1 关注用户

**POST** `/social/follow/{user_id}`

响应:
```json
{
    "code": 200,
    "message": "关注成功",
    "data": {
        "following_id": 2,
        "following_username": "李诗人",
        "is_mutual": false
    }
}
```

### 8.2 取消关注

**DELETE** `/social/follow/{user_id}`

响应:
```json
{
    "code": 200,
    "message": "取消关注成功"
}
```

### 8.3 获取关注列表

**GET** `/social/following?user_id=1&page=1&page_size=20`

查询参数:
- user_id: 目标用户ID（不传则为当前用户）
- page: 页码
- page_size: 每页数量

响应:
```json
{
    "code": 200,
    "data": {
        "items": [
            {
                "user_id": 2,
                "username": "李诗人",
                "nickname": "诗仙后人",
                "avatar_url": null,
                "bio": "热爱诗词",
                "level": 5,
                "is_mutual": true,
                "followed_at": "2026-03-08T10:00:00Z"
            }
        ],
        "total": 20,
        "page": 1,
        "page_size": 20
    }
}
```

### 8.4 获取粉丝列表

**GET** `/social/followers?user_id=1&page=1&page_size=20`

查询参数:
- user_id: 目标用户ID（不传则为当前用户）
- page: 页码
- page_size: 每页数量

响应:
```json
{
    "code": 200,
    "data": {
        "items": [
            {
                "user_id": 3,
                "username": "诗词爱好者",
                "nickname": "词客",
                "avatar_url": null,
                "bio": "学诗中",
                "level": 3,
                "is_following": true,
                "followed_at": "2026-03-08T10:00:00Z"
            }
        ],
        "total": 15,
        "page": 1,
        "page_size": 20
    }
}
```

### 8.5 获取用户公开资料

**GET** `/social/users/{user_id}/profile`

响应:
```json
{
    "code": 200,
    "data": {
        "user_id": 2,
        "username": "李诗人",
        "nickname": "诗仙后人",
        "avatar_url": null,
        "bio": "热爱诗词创作",
        "level": 5,
        "exp": 2500,
        "following_count": 10,
        "follower_count": 25,
        "work_count": 30,
        "is_following": false,
        "is_follower": false,
        "achievements": [
            {
                "id": 1,
                "code": "first_poem",
                "name": "初露锋芒",
                "description": "发布第一首作品",
                "icon": "first_poem",
                "rarity": "common",
                "unlocked_at": "2026-03-07T10:00:00Z"
            }
        ],
        "recent_works": [
            {
                "id": 1,
                "title": "春日即景",
                "genre": "五言绝句",
                "like_count": 10,
                "published_at": "2026-03-07T10:00:00Z"
            }
        ],
        "joined_at": "2026-03-01T10:00:00Z"
    }
}
```

### 8.6 获取动态消息流

**GET** `/social/feed?page=1&page_size=20`

查询参数:
- page: 页码
- page_size: 每页数量

响应:
```json
{
    "code": 200,
    "data": {
        "items": [
            {
                "id": 1,
                "type": "work_published",
                "user_id": 2,
                "username": "李诗人",
                "avatar_url": null,
                "content": "发布了新作品《春日即景》",
                "reference_id": 1,
                "reference_type": "work",
                "created_at": "2026-03-08T10:00:00Z"
            }
        ],
        "total": 100,
        "page": 1,
        "page_size": 20
    }
}
```

type 说明:
- work_published: 发布作品
- work_liked: 作品被点赞
- achievement_unlocked: 解锁成就
- relay_record: 接龙记录
- challenge_completed: 完成每日挑战
- level_up: 等级提升

## 9. 成就系统模块

### 9.1 获取所有成就定义

**GET** `/achievements`

响应:
```json
{
    "code": 200,
    "data": {
        "categories": [
            {
                "category": "learning",
                "category_name": "学海无涯",
                "achievements": [
                    {
                        "id": 1,
                        "code": "poem_reader_10",
                        "name": "初窥门径",
                        "description": "阅读10首诗词",
                        "icon": "poem_reader_10",
                        "rarity": "common",
                        "condition_type": "poems_read",
                        "condition_value": 10,
                        "exp_reward": 50,
                        "points_reward": 10
                    }
                ]
            },
            {
                "category": "creation",
                "category_name": "妙笔生花",
                "achievements": []
            },
            {
                "category": "social",
                "category_name": "高山流水",
                "achievements": []
            },
            {
                "category": "challenge",
                "category_name": "过关斩将",
                "achievements": []
            },
            {
                "category": "relay",
                "category_name": "珠联璧合",
                "achievements": []
            }
        ]
    }
}
```

rarity 说明:
- common: 普通
- rare: 稀有
- epic: 史诗
- legendary: 传说

### 9.2 获取用户成就列表

**GET** `/achievements/mine`

响应:
```json
{
    "code": 200,
    "data": {
        "unlocked": [
            {
                "id": 1,
                "code": "first_poem",
                "name": "初露锋芒",
                "description": "发布第一首作品",
                "icon": "first_poem",
                "rarity": "common",
                "category": "creation",
                "exp_reward": 50,
                "points_reward": 10,
                "unlocked_at": "2026-03-07T10:00:00Z"
            }
        ],
        "total_unlocked": 5,
        "total_achievements": 30,
        "completion_rate": 16.7
    }
}
```

### 9.3 获取成就进度

**GET** `/achievements/progress`

响应:
```json
{
    "code": 200,
    "data": {
        "progress": [
            {
                "achievement_id": 2,
                "code": "poem_reader_50",
                "name": "博览群书",
                "description": "阅读50首诗词",
                "icon": "poem_reader_50",
                "rarity": "rare",
                "current_value": 35,
                "target_value": 50,
                "percentage": 70.0,
                "is_unlocked": false
            }
        ]
    }
}
```

## 10. 平台统计模块

### 10.1 获取平台统计数据

**GET** `/stats/platform`

响应:
```json
{
    "total_poems": 157876,
    "tang_poems": 115770,
    "song_poems": 42106,
    "total_users": 1000
}
```

## 11. 诗词关系图谱模块

### 11.1 获取图谱数据

**GET** `/graph/data?dynasty=唐&category=思乡&min_poems=3`

查询参数:
- dynasty: 朝代筛选（可选）
- category: 题材筛选（可选）
- min_poems: 诗人最低收录诗作数量门槛（默认3，范围1-50）

响应:
```json
{
    "nodes": [
        {
            "id": "dynasty_唐",
            "name": "唐",
            "category": 0,
            "value": 5000,
            "symbolSize": 60,
            "dynasty": null,
            "poem_count": 5000,
            "representative_work": null
        },
        {
            "id": "author_李白",
            "name": "李白",
            "category": 1,
            "value": 120,
            "symbolSize": 40,
            "dynasty": "唐",
            "poem_count": 120,
            "representative_work": "静夜思"
        },
        {
            "id": "category_思乡",
            "name": "思乡",
            "category": 2,
            "value": 300,
            "symbolSize": 35,
            "dynasty": null,
            "poem_count": 300,
            "representative_work": null
        }
    ],
    "links": [
        {
            "source": "author_李白",
            "target": "dynasty_唐",
            "value": 120,
            "label": "李白·唐"
        },
        {
            "source": "author_李白",
            "target": "category_思乡",
            "value": 15,
            "label": "李白·思乡"
        },
        {
            "source": "author_李白",
            "target": "author_杜甫",
            "value": 3,
            "label": "同代·同题"
        }
    ],
    "categories": [
        {"name": "朝代"},
        {"name": "诗人"},
        {"name": "题材"}
    ]
}
```

节点 category 说明:
- 0: 朝代节点（苍黄色）
- 1: 诗人节点（朱砂色）
- 2: 题材节点（石绿色）

连线类型:
- 诗人→朝代: 诗人所属朝代
- 诗人→题材: 诗人擅长的题材
- 诗人→诗人: 同朝代且有共同题材的诗人

### 11.2 获取朝代简介

**GET** `/graph/dynasty-profiles`

说明: 返回预定义的朝代详细介绍数据（时间范围、代表诗人、诗风特点等）。

### 11.3 获取诗人简介

**GET** `/graph/poet-profiles`

说明: 返回预定义的知名诗人详细介绍数据（生平、风格、代表作等）。

### 11.4 获取诗人关系

**GET** `/graph/poet-relations`

说明: 返回预定义的诗人间关系数据（师徒、友人、同朝等关系）。

### 11.5 获取朝代列表

**GET** `/graph/dynasties`

响应:
```json
[
    {"name": "唐", "count": 50000},
    {"name": "宋", "count": 30000},
    {"name": "明", "count": 10000}
]
```

### 11.6 获取题材列表

**GET** `/graph/categories`

响应:
```json
[
    {"name": "思乡", "count": 3000},
    {"name": "山水", "count": 2500},
    {"name": "边塞", "count": 1200}
]
```

### 11.7 获取诗人详情

**GET** `/graph/author/{author_name}`

路径参数:
- author_name: 诗人名称（需URL编码）

响应:
```json
{
    "name": "李白",
    "dynasty": "唐",
    "poem_count": 120,
    "categories": ["思乡", "山水", "饮酒", "友情"],
    "representative_poems": [
        {
            "id": 1,
            "title": "静夜思",
            "content": "床前明月光，疑是地上霜。举头望明月，低头思故乡。"
        },
        {
            "id": 2,
            "title": "将进酒",
            "content": "君不见，黄河之水天上来，奔流到海不复回。君不见，高堂明镜悲白发..."
        }
    ]
}
```

## 12. 限时挑战模块

### 12.1 开始挑战

**POST** `/timed-challenge/start`

请求体:
```json
{
    "difficulty": "easy|medium|hard",
    "question_count": 5,
    "question_type": "mixed|fill_verse|author_guess|verse_match"
}
```

响应:
```json
{
    "session_id": 1,
    "total_questions": 5,
    "time_per_question": 15,
    "first_question": {
        "index": 0,
        "question_type": "fill_verse",
        "question_text": ""春眠不觉晓，"的下一句是？",
        "options": [
            {"key": "A", "text": "处处闻啼鸟"},
            {"key": "B", "text": "夜来风雨声"},
            {"key": "C", "text": "花落知多少"},
            {"key": "D", "text": "春来发几枝"}
        ],
        "time_limit": 15
    }
}
```

### 12.2 提交答案

**POST** `/timed-challenge/answer`

请求体:
```json
{
    "session_id": 1,
    "question_index": 0,
    "answer": "A",
    "time_spent": 5
}
```

响应:
```json
{
    "is_correct": true,
    "correct_answer": "处处闻啼鸟",
    "score_gained": 15,
    "combo": 1,
    "total_score": 15,
    "correct_count": 1,
    "answered_count": 1,
    "poem_title": "春晓",
    "poem_author": "孟浩然",
    "next_question": {},
    "is_finished": false
}
```

### 12.3 结束挑战

**POST** `/timed-challenge/end`

请求体:
```json
{
    "session_id": 1
}
```

响应:
```json
{
    "session_id": 1,
    "total_score": 120,
    "correct_count": 4,
    "total_questions": 5,
    "accuracy": 80,
    "max_combo": 3,
    "duration": 45,
    "exp_gained": 12,
    "answers": []
}
```

### 12.4 挑战历史

**GET** `/timed-challenge/history?page=1&page_size=20`

响应:
```json
{
    "items": [],
    "total": 10,
    "total_games": 10,
    "best_score": 200,
    "best_accuracy": 90
}
```

### 12.5 挑战排行榜

**GET** `/timed-challenge/rankings?period=all&page=1&page_size=50`

period 可选值: `today`, `week`, `all`

响应:
```json
{
    "items": [
        {
            "rank": 1,
            "user_id": 1,
            "username": "admin",
            "total_score": 500,
            "total_games": 10,
            "best_score": 200,
            "best_accuracy": 90
        }
    ],
    "total": 1
}
```

### 12.6 难度配置

| 难度 | 每题时间 | 最短内容长度 |
|------|---------|------------|
| easy | 20s | 10字 |
| medium | 15s | 15字 |
| hard | 10s | 20字 |

### 12.7 计分规则

- 基础分: easy=8, medium=12, hard=16（答错为0）
- 时间加分: 剩余时间占比 × 基础分 × 0.5
- 连击加分: combo × 2（上限20）

## 13. 飞花令模块

### 13.1 开始游戏

**POST** `/feihualing/start`

请求体:
```json
{
    "difficulty": 10,
    "keyword": "春"
}
```

字段说明:
- difficulty: 目标轮数（5/10/15，对应三级难度）
- keyword: 指定关键字（可选，不传则随机选取）

响应:
```json
{
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "keyword": "春",
    "time_limit": 30,
    "target_rounds": 10,
    "ai_first_round": {
        "verse": "春眠不觉晓",
        "poem_title": "春晓",
        "author": "孟浩然",
        "dynasty": "唐",
        "round_number": 1,
        "verified": true
    }
}
```

### 13.2 提交诗句

**POST** `/feihualing/submit`

请求体:
```json
{
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "poem_content": "春风又绿江南岸",
    "response_time": 15,
    "target_rounds": 10
}
```

响应:
```json
{
    "valid": true,
    "message": "匹配成功",
    "continue_game": true,
    "user_score": 120,
    "ai_score": 80,
    "round_number": 3,
    "score_gained": 15,
    "combo": 2,
    "user_round_count": 2,
    "poem_author": "王安石",
    "poem_title": "泊船瓜洲",
    "poem_dynasty": "宋",
    "ai_round": {
        "verse": "春江潮水连海平",
        "poem_title": "春江花月夜",
        "author": "张若虚",
        "dynasty": "唐",
        "round_number": 4,
        "verified": true
    },
    "ai_failed": false
}
```

### 13.3 获取提示

**GET** `/feihualing/hint/{game_id}`

响应:
```json
{
    "hint": "春█████",
    "author": "王维",
    "hint_cost": 5
}
```

### 13.4 结束游戏

**POST** `/feihualing/end`

请求体:
```json
{
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "reason": "completed"
}
```

reason 可选值: completed / timeout / give_up

响应:
```json
{
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "result": "win",
    "user_score": 120,
    "ai_score": 80,
    "total_rounds": 10,
    "user_round_count": 5,
    "keyword": "春",
    "duration": 180,
    "rounds": [
        {
            "round_number": 1,
            "player": "ai",
            "poem_content": "春眠不觉晓",
            "author": "孟浩然",
            "title": "春晓",
            "dynasty": "唐",
            "created_at": "2026-03-08T10:00:00Z"
        }
    ]
}
```

### 13.5 获取历史记录

**GET** `/feihualing/history?page=1&page_size=10`

响应:
```json
{
    "items": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "keyword": "春",
            "result": "win",
            "user_score": 120,
            "ai_score": 80,
            "total_rounds": 10,
            "difficulty": 10,
            "created_at": "2026-03-08T10:00:00Z"
        }
    ],
    "total": 20,
    "page": 1,
    "page_size": 10
}
```

## 14. 评论模块

### 14.1 发表评论

**POST** `/works/{work_id}/comments`

请求体:
```json
{
    "content": "这首诗意境深远，赞！",
    "parent_id": null
}
```

字段说明:
- content: 评论内容（1-500字）
- parent_id: 父评论 ID（回复时传，顶级评论为 null）

响应:
```json
{
    "id": 1,
    "work_id": 1,
    "user_id": 1,
    "username": "诗人",
    "nickname": "妙笔生花",
    "avatar_url": null,
    "parent_id": null,
    "reply_to_username": null,
    "content": "这首诗意境深远，赞！",
    "like_count": 0,
    "is_liked": false,
    "created_at": "2026-03-08T10:00:00Z",
    "replies": []
}
```

### 14.2 获取评论列表

**GET** `/works/{work_id}/comments?page=1&page_size=20`

响应:
```json
{
    "items": [
        {
            "id": 1,
            "work_id": 1,
            "user_id": 1,
            "username": "诗人",
            "nickname": "妙笔生花",
            "avatar_url": null,
            "parent_id": null,
            "reply_to_username": null,
            "content": "这首诗意境深远，赞！",
            "like_count": 5,
            "is_liked": true,
            "created_at": "2026-03-08T10:00:00Z",
            "replies": [
                {
                    "id": 2,
                    "work_id": 1,
                    "user_id": 2,
                    "username": "词客",
                    "nickname": null,
                    "avatar_url": null,
                    "parent_id": 1,
                    "reply_to_username": "诗人",
                    "content": "深有同感！",
                    "like_count": 0,
                    "is_liked": false,
                    "created_at": "2026-03-08T10:05:00Z",
                    "replies": []
                }
            ]
        }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20
}
```

### 14.3 删除评论

**DELETE** `/works/{work_id}/comments/{comment_id}`

说明: 评论作者或作品主可删除。

响应:
```json
{
    "code": 200,
    "message": "评论已删除"
}
```

### 14.4 点赞评论

**POST** `/works/{work_id}/comments/{comment_id}/like`

响应:
```json
{
    "code": 200,
    "message": "点赞成功",
    "like_count": 6
}
```

### 14.5 取消点赞评论

**DELETE** `/works/{work_id}/comments/{comment_id}/like`

响应:
```json
{
    "code": 200,
    "message": "取消点赞成功",
    "like_count": 5
}
```

## 15. AI服务模块

### 15.1 AI对话

**POST** `/ai/chat`

请求体:
```json
{
    "prompt": "请解释李白的诗风特点",
    "system_prompt": "你是一位诗词学者",
    "temperature": 0.7,
    "max_tokens": 2048
}
```

响应:
```json
{
    "content": "李白的诗风豪放飘逸...",
    "model": "qwen-plus"
}
```

### 15.2 AI评分

**POST** `/ai/score`

请求体:
```json
{
    "question": "春风_柳绿",
    "correct_answers": ["拂", "摇"],
    "user_answer": "拂"
}
```

响应:
```json
{
    "score": 88,
    "accuracy_score": 95,
    "artistic_score": 85,
    "diction_score": 84,
    "feedback": "'拂'用得很有意境，富有诗意。",
    "is_correct": true
}
```

### 15.3 AI辅助创作

**POST** `/ai/creation`

请求体:
```json
{
    "context": "春风拂柳绿，桃花映日红",
    "mode": "continue",
    "keywords": ["春", "花"]
}
```

mode 说明:
- continue: 续写下一句
- inspire: 提供创作灵感
- generate: 生成完整诗词
- theme: 按主题生成

响应:
```json
{
    "content": "莺歌燕舞处，诗意满园中",
    "explanation": "续写以莺歌燕舞呼应春景...",
    "suggestions": ["可考虑用“蝶”替代“燕”"]
}
```

### 15.4 AI格律检查

**POST** `/ai/check-poem`

请求体:
```json
{
    "poem_text": "春风拂柳绿，桃花映日红。莺歌燕舞处，诗意满园中。"
}
```

响应:
```json
{
    "is_valid": true,
    "tone_analysis": [],
    "rhyme_analysis": {},
    "couplet_analysis": {},
    "issues": [],
    "suggestions": []
}
```

### 15.5 AI诗词赏析

**POST** `/ai/analyze-poem`

请求体:
```json
{
    "poem_text": "春风拂柳绿，桃花映日红。莺歌燕舞处，诗意满园中。"
}
```

响应:
```json
{
    "total_score": 85,
    "meter_score": 80,
    "artistic_score": 90,
    "diction_score": 85,
    "overall_score": 85,
    "highlights": ["对仗工整", "意境优美"],
    "improvements": ["第三句可更加精炼"],
    "appreciation": "整体意境优美，春意盎然..."
}
```

### 15.6 AI飞花令应答

**POST** `/ai/feihua-respond`

请求体:
```json
{
    "keyword": "春",
    "used_poems": ["春眠不觉晓"]
}
```

响应:
```json
{
    "verse": "春风又绿江南岸",
    "poem_title": "泊船瓜洲",
    "author": "王安石",
    "dynasty": "宋",
    "confidence": 0.95
}
```

### 15.7 AI诗词上下文查询

**POST** `/ai/poem-context`

请求体:
```json
{
    "title": "静夜思",
    "author": "李白",
    "dynasty": "唐",
    "content": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
    "genre": "五言绝句",
    "category": "思乡",
    "query_type": "author_bio"
}
```

query_type 说明:
- author_bio: 诗人小传
- deep_appreciation: 深度赏析
- allusions: 典故意象
- verse_analysis: 逐句精析
- free_qa: 自由问答（需传 question 字段）
- meter_analysis: 格律标注

响应:
```json
{
    "query_type": "author_bio",
    "content": "李白（701年—762年），字太白，号青莲居士...",
    "title": "诗仙李白",
    "sections": null,
    "lines": null,
    "rhyme_scheme": null,
    "meter_type": null
}
```

### 15.8 AI诗词多轮对话

**POST** `/ai/poem-chat`

请求体:
```json
{
    "title": "静夜思",
    "author": "李白",
    "dynasty": "唐",
    "content": "床前明月光...",
    "genre": "五言绝句",
    "category": "思乡",
    "history": [
        {"role": "user", "content": "这首诗表达了什么情感？"},
        {"role": "assistant", "content": "这首诗表达了深深的思乡之情..."}
    ],
    "message": "有没有类似主题的作品推荐？"
}
```

响应:
```json
{
    "reply": "有几首类似主题的作品...",
    "title": null
}
```

### 15.9 AI诗词流式对话

**POST** `/ai/poem-chat-stream`

请求体: 同 15.8

响应: Server-Sent Events (SSE) 流式返回，逐10字符推送。

```
data: {"content": "有几首类"}
data: {"content": "似主题的作品"}
data: {"content": "..."}
data: [DONE]
```

## 16. 数据模型说明

### 16.1 用户状态
- is_active: 用户是否激活
- level: 用户等级
- exp: 经验值
- points: 积分

### 16.2 作品状态
- draft: 草稿
- published: 已发布

### 16.3 挑战评分维度
- beauty_score: 意境美（0-100）
- creativity_score: 创意度（0-100）
- mood_score: 情感分（0-100）
- ai_score: AI综合评分（0-100）

### 16.4 作品评分维度
- ai_grammar_score: 格律评分（0-100）
- ai_artistic_score: 艺术评分（0-100）
- ai_total_score: 总评分（0-100）
- composite_score: 综合评分（考虑点赞、浏览、AI评分）

## 17. 错误响应示例

```json
{
    "detail": "错误信息描述"
}
```

常见错误:
- 400: "请求参数错误"
- 401: "未认证" / "用户名或密码错误"
- 403: "无权限"
- 404: "资源不存在"
- 500: "服务器内部错误"
