import yaml
import pysel
import logging
import random
from typing import Any, Dict, List

class GameService:
    def __init__(self, game_rules_path: str, repo: Any):
        self.repo = repo
        with open(game_rules_path, 'r') as f:
            self.game_rules = yaml.safe_load(f)
        self.elements_by_id = {elem['id']: elem for elem in self.game_rules.get('elements', [])}
        self.rewards_by_id = {reward['id']: reward for reward in self.game_rules.get('rewards', [])}
        self.helper_functions = self._compile_helpers()

    def _compile_helpers(self) -> Dict[str, Any]:
        helpers = {}
        for helper_def in self.game_rules.get('helpers', []):
            helper_id = helper_def['id']
            expression = helper_def['expression']
            arg_names = helper_def.get('args', [])

            def helper_wrapper(*args):
                context = {arg_name: arg_value for arg_name, arg_value in zip(arg_names, args)}
                def evaluate_with_context(extra_context: Dict[str, Any]):
                    full_context = {**extra_context, **context}
                    return pysel.Expression(expression).evaluate(full_context)
                return evaluate_with_context
            helpers[helper_id] = helper_wrapper
        return helpers

    def process_action(self, player_id: str, action: str) -> Dict[str, List[Dict]]:
        """
        Przetwarza akcję gracza i zwraca listę zdobytych nagród.
        """
        player = self.repo.get_player(player_id)
        rewards_earned = []
        
        item_ids = self.game_rules['actions_to_items_mapping'].get(action)
        if item_ids:
            if isinstance(item_ids, list):
                selected_item_id = self._get_random_item_by_rarity(item_ids)
            else:
                selected_item_id = item_ids
            
            if selected_item_id:
                player['inventory'][selected_item_id] = player['inventory'].get(selected_item_id, 0) + 1
                logging.info(f"Player {player_id} received item: {selected_item_id}")
                rewards_earned.append({"type": "item_received", "value": selected_item_id})

        facts = self._get_player_facts(player)
        
        for quest in self.game_rules['quests']:
            if quest['id'] not in player['completed_quests'] or quest['repeatable']:
                quest_rule = quest.get('rule')
                pysel_context = {**facts}
                for helper_id, helper_func in self.helper_functions.items():
                    pysel_context[helper_id] = lambda *args: helper_func(*args)(extra_context=facts)

                if pysel.Expression(quest_rule).evaluate(pysel_context):
                    reward_info = self.award_reward(player, quest['reward'])
                    if reward_info:
                        rewards_earned.append(reward_info)
                    if not quest['repeatable']:
                        player['completed_quests'].append(quest['id'])

        self.repo.save_player(player)
        return {"rewards": rewards_earned}

    def award_reward(self, player: dict, reward_id: str) -> Dict[str, Any] or None:
        reward = self.rewards_by_id.get(reward_id)
        if not reward:
            logging.error(f"Reward with id {reward_id} not found.")
            return None

        if reward['type'] == 'title':
            if reward['value'] not in player['titles']:
                player['titles'].append(reward['value'])
                logging.info(f"Player earned title: {reward['value']}")
                return {"type": "title_earned", "value": reward['value'], "message": reward.get('message')}
        elif reward['type'] == 'currency':
            player['currency'] = player.get('currency', 0) + reward['value']
            logging.info(f"Player received {reward['value']} currency.")
            return {"type": "currency_received", "value": reward['value'], "message": reward.get('message')}
        
        return None

    def _get_player_facts(self, player: dict) -> Dict[str, Any]:
        rarity_counts = {}
        for item_id, count in player['inventory'].items():
            item_data = self.elements_by_id.get(item_id)
            if item_data and 'rarity' in item_data:
                rarity = item_data['rarity']
                rarity_counts[rarity] = rarity_counts.get(rarity, 0) + count
        
        return {
            'inventory': player.get('inventory', {}),
            'titles': player.get('titles', []),
            'rarity_counts': rarity_counts,
            'currency': player.get('currency', 0)
        }

    def _get_random_item_by_rarity(self, item_ids: list):
        items_with_rarity = []
        for item_id in item_ids:
            item_data = self.elements_by_id.get(item_id)
            if item_data and 'rarity' in item_data:
                rarity = item_data['rarity']
                prob = self.game_rules['rarity_probabilities'].get(rarity, 0)
                items_with_rarity.append((item_id, prob))

        total_prob = sum(prob for _, prob in items_with_rarity)
        if total_prob == 0:
            return None
        
        probabilities = [prob / total_prob for _, prob in items_with_rarity]
        return random.choices([item_id for item_id, _ in items_with_rarity], weights=probabilities, k=1)[0]
