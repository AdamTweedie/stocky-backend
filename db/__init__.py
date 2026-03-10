from .connection import get_connection, create_tables

from .stocks import (
    insert_stock,
    get_all_stocks,
    get_stock_by_short_name,
    get_stocks_by_filter,
    update_stock,
    delete_stock,
    get_stocks_table_size,
    bulk_insert_stocks,
)

from .news import (
    insert_news,
    get_all_news,
    get_news_by_recency,
    get_news_by_sentiment,
    get_news_by_short_name,
    get_news_by_title,
    update_news_by_id,
    update_news_by_title,
    update_ai_summary_by_short_name,
    delete_news_older_than,
)

from .users import (
    create_user_email,
    create_user_google,
    login_email,
    get_user_by_session,
    logout,
    get_user_by_id,
    get_user_by_email,
    get_user_by_google_id,
    get_users_by_tier,
    get_all_users,
    update_user_profile,
    update_password,
    verify_email,
    set_reset_token,
    reset_password,
    update_subscription,
    cancel_subscription,
    downgrade_expired_subscriptions,
    increment_ai_tokens,
    reset_ai_tokens,
    get_token_usage,
    deactivate_user,
    reactivate_user,
    set_admin,
    delete_user,
)

from .user_follows import (
    follow_stock,
    unfollow_stock,
    get_followed_stocks,
    reorder_stocks,
    follow_industry,
    unfollow_industry,
    get_followed_industries,
    get_user_feed_filters,
    get_active_short_names,
)

