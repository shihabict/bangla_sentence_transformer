from sentence_transformers import SentenceTransformer, LoggingHandler, models, evaluation, losses, util
from torch.utils.data import DataLoader
from sentence_transformers.datasets import ParallelSentencesDataset
import os
import logging
import numpy as np


class BNSentenceTransformer:

    def train(self, path):
        logging.basicConfig(format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            level=logging.INFO,
                            handlers=[LoggingHandler()])

        teacher_model_name = 'stsb-xlm-r-multilingual'
        student_model_name = 'xlm-roberta-base'

        max_seq_length = 128  # Student model max. lengths for inputs (number of word pieces)
        train_batch_size = 64  # Batch size for training
        inference_batch_size = 64  # Batch size at inference
        max_sentences_per_language = 500000  # Maximum number of  parallel sentences for training
        train_max_sentence_length = 250  # Maximum length (characters) for parallel training sentences

        num_epochs = 1  # Train for x epochs
        num_warmup_steps = 10000  # Warumup steps

        num_evaluation_steps = 500

        output_path = "output/bangla-sentence-transformer"
        logging.info("Load teacher model")
        teacher_model = SentenceTransformer(teacher_model_name)
        logging.info("Create student model from scratch")
        word_embedding_model = models.Transformer(student_model_name, max_seq_length=max_seq_length)
        pooling_model = models.Pooling(word_embedding_model.get_word_embedding_dimension())
        student_model = SentenceTransformer(student_model_name)
        train_data = ParallelSentencesDataset(student_model=student_model, teacher_model=teacher_model,
                                              batch_size=inference_batch_size, use_embedding_cache=False)
        train_data.load_data(path, max_sentences=max_sentences_per_language,
                             max_sentence_length=train_max_sentence_length)
        train_dataloader = DataLoader(train_data, shuffle=True, batch_size=train_batch_size)
        train_loss = losses.MSELoss(model=student_model)

        #### Evaluate cross-lingual performance on different tasks #####
        evaluators = []  # evaluators has a list of different evaluator classes we call periodically
        src_sentences = []
        trg_sentences = []
        cnt = 0
        with open(path, 'r') as fIn:
            for line in fIn:
                splits = line.strip().split('\t')
                if len(splits) != 2:
                    continue
                if splits[0] != "" and splits[1] != "":
                    src_sentences.append(splits[0])
                    trg_sentences.append(splits[1])
                cnt += 1
                if cnt >= num_evaluation_steps:
                    break

        logging.info("MSE Evaluation is Ready")

        # Mean Squared Error (MSE) measures the (euclidean) distance between teacher and student embeddings
        dev_mse = evaluation.MSEEvaluator(src_sentences, trg_sentences, name=os.path.basename(path),
                                          teacher_model=teacher_model, batch_size=inference_batch_size)
        evaluators.append(dev_mse)
        logging.info('Evaluation appended')

        logging.info('Student Model training is going to start')
        # Train the model
        student_model.fit(train_objectives=[(train_dataloader, train_loss)],
                          evaluator=evaluation.SequentialEvaluator(evaluators,
                                                                   main_score_function=lambda scores: np.mean(scores)),
                          epochs=num_epochs,
                          warmup_steps=num_warmup_steps,
                          evaluation_steps=num_evaluation_steps,
                          output_path=output_path,
                          save_best_model=True,
                          optimizer_params={'lr': 2e-5, 'eps': 1e-6}
                          )

    def train_new(self, path,number_of_sentences,output_path):
        logging.basicConfig(format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            level=logging.INFO,
                            handlers=[LoggingHandler()])

        teacher_model_name = 'stsb-xlm-r-multilingual'
        student_model_name = 'xlm-roberta-base'

        max_seq_length = 128  # Student model max. lengths for inputs (number of word pieces)
        train_batch_size = 32  # Batch size for training
        inference_batch_size = 32  # Batch size at inference
        if number_of_sentences == 'Full_data':
            max_sentences_per_language = None
        else:
            max_sentences_per_language = number_of_sentences  # Maximum number of  parallel sentences for training
        # max_sentences_per_language = 10  # Maximum number of  parallel sentences for training
        train_max_sentence_length = 250  # Maximum length (characters) for parallel training sentences

        num_epochs = 10  # Train for x epochs
        num_warmup_steps = 8000  # Warumup steps

        num_evaluation_steps = 500

        # output_path = "bengal_transformer"
        logging.info("Load teacher model")
        teacher_model = SentenceTransformer(teacher_model_name,device='cuda')
        logging.info("Create student model from scratch")
        word_embedding_model = models.Transformer(student_model_name, max_seq_length=max_seq_length)
        pooling_model = models.Pooling(word_embedding_model.get_word_embedding_dimension())
        student_model = SentenceTransformer(modules=[word_embedding_model, pooling_model])
        train_data = ParallelSentencesDataset(student_model=student_model, teacher_model=teacher_model,
                                              batch_size=inference_batch_size, use_embedding_cache=False)
        train_data.load_data(path, max_sentences=max_sentences_per_language,
                             max_sentence_length=train_max_sentence_length)
        train_dataloader = DataLoader(train_data, shuffle=True, batch_size=train_batch_size)
        train_loss = losses.MSELoss(model=student_model)

        #### Evaluate cross-lingual performance on different tasks #####
        evaluators = []  # evaluators has a list of different evaluator classes we call periodically
        src_sentences = []
        trg_sentences = []
        cnt = 0
        with open(path, 'r') as fIn:
            for line in fIn:
                splits = line.strip().split('###')
                if len(splits) != 2:
                    continue
                if splits[0] != "" and splits[1] != "":
                    src_sentences.append(splits[0])
                    trg_sentences.append(splits[1])
                cnt += 1
                if cnt >= num_evaluation_steps:
                    break

        logging.info("MSE Evaluation is Ready")

        # Mean Squared Error (MSE) measures the (euclidean) distance between teacher and student embeddings
        dev_mse = evaluation.MSEEvaluator(src_sentences, trg_sentences, name=os.path.basename(path),
                                          teacher_model=teacher_model, batch_size=inference_batch_size)
        evaluators.append(dev_mse)
        logging.info('Evaluation appended')

        logging.info('Student Model training is going to start')
        student_model.device
        # Train the model
        student_model.fit(train_objectives=[(train_dataloader, train_loss)],
                          evaluator=evaluation.SequentialEvaluator(evaluators,
                                                                   main_score_function=lambda scores: np.mean(scores)),
                          epochs=num_epochs,
                          warmup_steps=num_warmup_steps,
                          evaluation_steps=num_evaluation_steps,
                          output_path=output_path,
                          save_best_model=True,
                          optimizer_params={'lr': 2e-5, 'eps': 1e-6}
                          )
        student_model.save(output_path)
        # print(student_model.best_score)


if __name__ == '__main__':
    transformer = BNSentenceTransformer()

    path = 'DATA/dataset.txt'
    transformer.train_new(path)