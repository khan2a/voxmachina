#!/usr/bin/env python3
"""
Transcript Viewer CLI Tool
View and export call transcripts from Happy Medical Centre
"""
import argparse
import json
import sys

from src.transcript_storage import TranscriptStorage


def view_transcript(storage: TranscriptStorage, call_id: str):
    """View full transcript for a call"""
    transcript = storage.get_full_transcript(call_id)

    if not transcript:
        print(f"❌ No transcript found for call: {call_id}")
        return

    print(f"\n{'='*60}")
    print(f"📞 Call Transcript: {call_id}")
    print(f"{'='*60}\n")
    print(transcript)
    print(f"\n{'='*60}\n")


def view_summary(storage: TranscriptStorage, call_id: str):
    """View AI summary for a call"""
    summary_data = storage.get_call_summary(call_id)

    if not summary_data:
        print(f"❌ No summary found for call: {call_id}")
        return

    print(f"\n{'='*60}")
    print(f"📊 Call Summary: {call_id}")
    print(f"{'='*60}\n")
    print(f"Agent: {summary_data.get('agent_name', 'Unknown')}")
    print(f"Created: {summary_data.get('created_at', 'Unknown')}")

    # Display sentiment analysis if available
    if summary_data.get("sentiment_analysis"):
        try:
            sentiment = json.loads(summary_data["sentiment_analysis"])
            overall = summary_data.get("overall_sentiment", "unknown")

            # Emoji mapping for sentiment
            sentiment_emoji = {"positive": "😊", "neutral": "😐", "negative": "😟", "urgent": "🚨"}
            emoji = sentiment_emoji.get(overall, "❓")

            print("\n🎭 Sentiment Analysis:")
            print(
                f"  Overall: {emoji} {overall.upper()} "
                f"({sentiment.get('confidence', 0)}% confidence)"
            )

            if sentiment.get("key_emotions"):
                emotions = ", ".join(sentiment["key_emotions"])
                print(f"  Emotions: {emotions}")

            if sentiment.get("satisfaction"):
                print(f"  Satisfaction: {sentiment['satisfaction']}")

            if sentiment.get("concerns"):
                concerns = ", ".join(sentiment["concerns"])
                print(f"  ⚠️  Concerns: {concerns}")
        except Exception as e:
            print(f"  (Sentiment data unavailable: {e})")

    print("\n📝 Summary:")
    print(f"{summary_data.get('summary', 'No summary available')}")
    print(f"\n{'='*60}\n")


def export_call(storage: TranscriptStorage, call_id: str, output_path: str = None):
    """Export call data to JSON file"""
    result = storage.export_call_data(call_id, output_path)

    if result:
        print(f"✅ Call data exported to: {result}")
    else:
        print(f"❌ Failed to export call: {call_id}")


def list_recent_calls(storage: TranscriptStorage, limit: int = 10):
    """List recent calls with transcripts"""
    import sqlite3

    try:
        conn = sqlite3.connect(storage.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT DISTINCT call_id, agent_name, MIN(timestamp) as first_message
            FROM transcripts
            GROUP BY call_id
            ORDER BY first_message DESC
            LIMIT ?
        """,
            (limit,),
        )

        calls = cursor.fetchall()
        conn.close()

        if not calls:
            print("📭 No calls found in database")
            return

        print(f"\n📞 Recent Calls (Last {limit}):")
        print(f"{'='*60}")
        for call_id, agent, timestamp in calls:
            print(f"  • {call_id}")
            print(f"    Agent: {agent} | Time: {timestamp}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"❌ Error listing calls: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="View and export Happy Medical Centre call transcripts"
    )

    parser.add_argument("--call-id", help="Call ID to view/export")

    parser.add_argument("--transcript", action="store_true", help="View full transcript")

    parser.add_argument("--summary", action="store_true", help="View AI-generated summary")

    parser.add_argument("--export", metavar="PATH", help="Export call data to JSON file")

    parser.add_argument("--list", action="store_true", help="List recent calls")

    parser.add_argument(
        "--limit", type=int, default=10, help="Number of recent calls to list (default: 10)"
    )

    parser.add_argument(
        "--db-path",
        default="data/transcripts.db",
        help="Path to transcript database (default: data/transcripts.db)",
    )

    args = parser.parse_args()

    # Initialize storage
    storage = TranscriptStorage(db_path=args.db_path)

    # List recent calls
    if args.list:
        list_recent_calls(storage, args.limit)
        return

    # Require call_id for other operations
    if not args.call_id:
        print("❌ Error: --call-id is required (or use --list to see recent calls)")
        parser.print_help()
        sys.exit(1)

    # View transcript
    if args.transcript:
        view_transcript(storage, args.call_id)

    # View summary
    if args.summary:
        view_summary(storage, args.call_id)

    # Export call
    if args.export:
        export_call(storage, args.call_id, args.export)

    # Default: show both transcript and summary
    if not (args.transcript or args.summary or args.export):
        view_transcript(storage, args.call_id)
        view_summary(storage, args.call_id)


if __name__ == "__main__":
    main()
