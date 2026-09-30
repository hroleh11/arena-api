from datetime import datetime
import logging

from column.celery import app

logger = logging.getLogger(__name__)


@app.task(name="api.tasks.fetch_lineup_data")
def fetch_lineup_data(news_pk, lineup_global_id):
    """Send request to vylo-props for lineup data"""
    request_data = {
        "news_pk": news_pk,
        "lineup_global_id": lineup_global_id,
        "service": "column-api",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        app.send_task(
            "vylo_bets.tasks.fetch_lineup_data_request",
            args=[request_data],
            queue="lineup_priority"  # Dedicated high-priority queue for lineup data
        )
    except Exception as e:
        logger.error(f"Failed to send lineup data request for news {news_pk}: {e}")
        raise


@app.task(name="api.tasks.receive_lineup_data")
def receive_lineup_data(response_data):
    """Process lineup data received from vylo-props"""
    from api.models import ColumnNews
    
    news_pk = response_data.get("news_pk")
    lineup_global_id = response_data.get("lineup_global_id")
    success = response_data.get("success", False)
    
    if success:
        lineup_data = response_data.get("lineup_data")
        if lineup_data:
            try:
                news_instance = ColumnNews.objects.get(pk=news_pk)
                if news_instance.lineup_data:
                    logger.info(f"ColumnNews {news_pk} already has lineup_data, skipping update")
                    return
                news_instance.lineup_data = lineup_data
                news_instance.save(update_fields=['lineup_data'])
                
                logger.info(f"Successfully updated lineup data for ColumnNews {news_pk}")
                                      
            except ColumnNews.DoesNotExist:
                logger.error(f"ColumnNews with pk {news_pk} not found")
            except Exception as e:
                logger.error(f"Error updating ColumnNews {news_pk}: {str(e)}", exc_info=True)
        else:
            logger.warning(f"Received empty lineup_data for news {news_pk}")
    else:
        error_msg = response_data.get('error', 'Unknown error')
        logger.error(f"Error fetching lineup data for news {news_pk}: {error_msg}")